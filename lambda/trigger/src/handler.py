import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_incident(event):
    """Pull {cluster, namespace, pod} out of a CloudWatch alarm state change.

    The alarm event carries dimensions nested under the metric definition, not
    as a flat pod name:
      detail.configuration.metrics[].metricStat.metric.dimensions
    """
    detail = event.get("detail", {})
    dimensions = {}

    for metric in detail.get("configuration", {}).get("metrics", []):
        dims = metric.get("metricStat", {}).get("metric", {}).get("dimensions")
        if dims:
            dimensions = dims
            break

    return {
        "cluster": dimensions.get("ClusterName"),
        "namespace": dimensions.get("Namespace"),
        # PodName is the stable deployment-level name, not the restarting pod.
        "pod": dimensions.get("PodName"),
        "alarm": detail.get("alarmName"),
        "reason": detail.get("state", {}).get("reason"),
        "fired_at": detail.get("state", {}).get("timestamp"),
    }


def invoke_agent(incident):
    """Invoke the AgentCore runtime and return its report."""
    client = boto3.client("bedrock-agentcore")
    response = client.invoke_agent_runtime(
        agentRuntimeArn=os.environ["AGENT_RUNTIME_ARN"],
        contentType="application/json",
        accept="application/json",
        payload=json.dumps(
            {
                "cluster": incident["cluster"],
                "namespace": incident["namespace"],
                "pod": incident["pod"],
            }
        ).encode("utf-8"),
    )

    # response is a streaming body, not a dict.
    body = response["response"].read()
    return json.loads(body)


def format_report(incident, report):
    """Render the JSON report as readable text for email and Slack.
    """
    lines = [
        "{}/{} - container restart investigated".format(
            incident.get("namespace"), incident.get("pod")
        ),
        "",
        "Root cause: {}".format(report.get("root_cause", "unknown")),
        "Confidence: {}".format(report.get("confidence", "unknown")),
        "",
    ]

    evidence = report.get("evidence") or []
    if evidence:
        lines.append("Evidence ({}):".format(len(evidence)))
        for item in evidence:
            lines.append("  - [{}] {}".format(item.get("tool"), item.get("finding")))
        lines.append("")

    missing = report.get("missing_evidence") or []
    lines.append("Missing evidence: {}".format("; ".join(missing) if missing else "none"))

    refs = report.get("runbook_references") or []
    if refs:
        lines.append("")
        lines.append("Runbook ({} refs):".format(len(refs)))
        for ref in refs:
            lines.append("  - {}".format(ref))

    steps = report.get("recommended_next_steps") or []
    if steps:
        lines.append("")
        lines.append("Recommended (advisory only):")
        for step in steps:
            lines.append("  - {}".format(step))

    commands = report.get("verification_commands") or []
    if commands:
        lines.append("")
        lines.append("Verify:")
        for cmd in commands:
            lines.append("  {}".format(cmd))

    lines.append("")
    lines.append(
        "No remediation was executed."
        if report.get("remediation_executed") is False
        else "WARNING: remediation_executed was not false."
    )
    return "\n".join(lines)


def slack_payload(incident, report):
    """Wrap the report in Amazon Q's custom notification schema.
    """
    return {
        "version": "1.0",
        "source": "custom",
        "content": {
            "title": "{}: {}/{}".format(
                report.get("root_cause", "Container restart")[:60],
                incident.get("namespace"),
                incident.get("pod"),
            ),
            "description": format_report(incident, report),
        },
    }


def publish_report(incident, report):
    """Send the formatted report to SNS."""
    topic = os.environ.get("SNS_TOPIC_ARN")
    if not topic:
        logger.warning("SNS_TOPIC_ARN not set; report not published")
        return

    # publish topic
    boto3.client("sns").publish(
        TopicArn=topic,
        Subject="Incident: {}/{}".format(
            incident.get("namespace"), incident.get("pod")
        )[:100],
        Message=json.dumps(slack_payload(incident, report)),
    )


def handler(event, context):
    """Lambda entrypoint """
    # get incident
    incident = extract_incident(event)
    logger.info("incident_detected: %s", json.dumps(incident))

    missing = [k for k in ("cluster", "namespace", "pod") if not incident.get(k)]
    if missing:
        logger.error("missing identifiers %s in event: %s", missing, json.dumps(event))
        return {"ok": False, "missing": missing}

    # invoke agent
    try:
        result = invoke_agent(incident)
    except Exception as exc:    # when error, return
        logger.exception("agent invocation failed")
        return {"ok": False, "incident": incident, "error": str(exc)}

    report = result.get("response", result)
    logger.info("incident_report: %s", json.dumps(report))

    # publish
    try:
        publish_report(incident, report)
    except Exception:
        # The report is already in the logs, so a failed publish is degraded
        # delivery rather than a lost investigation.
        logger.exception("publishing report failed")

    return {"ok": True, "incident": incident, "report": report}
