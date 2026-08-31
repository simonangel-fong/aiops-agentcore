"""Parser tests against the real CloudWatch alarm event shape."""

import sys
from pathlib import Path


# Load the handler by path so that "src" is never claimed as a global package
# name -- app/, lambda/ and agent/ each have one.
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "trigger_handler", Path(__file__).resolve().parents[1] / "src" / "handler.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
extract_incident, handler = _mod.extract_incident, _mod.handler

# Shape from the AWS "CloudWatch Alarm State Change" schema, carrying the
# dimensions this project's alarm actually reports.
EVENT = {
    "source": "aws.cloudwatch",
    "detail-type": "CloudWatch Alarm State Change",
    "detail": {
        "alarmName": "aiops-agentcore-cluster-container-restart",
        "state": {
            "value": "ALARM",
            "reason": "Threshold Crossed: 1 datapoint [1.0 (29/08/26 19:10:00)]",
            "timestamp": "2026-08-29T19:11:50.431+0000",
        },
        "configuration": {
            "metrics": [
                {
                    "id": "m1",
                    "metricStat": {
                        "metric": {
                            "namespace": "ContainerInsights",
                            "name": "pod_number_of_container_restarts",
                            "dimensions": {
                                "ClusterName": "aiops-agentcore",
                                "Namespace": "incident-demo",
                                "PodName": "aiops-agentcore-workload",
                            },
                        },
                        "period": 60,
                        "stat": "Maximum",
                    },
                    "returnData": True,
                }
            ]
        },
    },
}


def test_extract_identifiers():
    incident = extract_incident(EVENT)
    assert incident["cluster"] == "aiops-agentcore"
    assert incident["namespace"] == "incident-demo"
    assert incident["pod"] == "aiops-agentcore-workload"
    assert incident["alarm"] == "aiops-agentcore-cluster-container-restart"


def test_handler_ok(monkeypatch):
    """The agent call is mocked: this asserts wiring, not AgentCore."""
    monkeypatch.setattr(
        _mod, "invoke_agent", lambda incident: {"response": {"root_cause": "OOMKilled"}}
    )
    result = handler(EVENT, None)
    assert result["ok"] is True
    assert result["incident"]["pod"] == "aiops-agentcore-workload"
    assert result["report"]["root_cause"] == "OOMKilled"


def test_handler_reports_agent_failure(monkeypatch):
    """A failed invocation must be reported, not swallowed -- the alarm has
    already fired, so a lost call means an incident with no report."""
    def boom(incident):
        raise RuntimeError("runtime unavailable")

    monkeypatch.setattr(_mod, "invoke_agent", boom)
    result = handler(EVENT, None)
    assert result["ok"] is False
    assert "runtime unavailable" in result["error"]


def test_handler_reports_missing_identifiers():
    """A malformed event must fail loudly, not invoke the agent with nulls."""
    result = handler({"detail": {"alarmName": "x"}}, None)
    assert result["ok"] is False
    assert set(result["missing"]) == {"cluster", "namespace", "pod"}


REPORT = {
    "root_cause": "The container was terminated by the kernel's cgroup OOM killer.",
    "confidence": "high",
    "evidence": [
        {"tool": "get_container_restart_info", "finding": "reason OOMKilled, exit 137"},
        {"tool": "get_resource_limits", "finding": "limit 256Mi"},
    ],
    "missing_evidence": [],
    "runbook_references": ["reason: OOMKilled is the decisive field"],
    "recommended_next_steps": ["Investigate the leak before raising the limit"],
    "verification_commands": ["kubectl describe pod -n incident-demo aiops-agentcore-workload"],
    "remediation_executed": False,
}

INCIDENT = {"cluster": "aiops-agentcore", "namespace": "incident-demo", "pod": "aiops-agentcore-workload"}


def test_format_report():
    text = _mod.format_report(INCIDENT, REPORT)
    assert "incident-demo/aiops-agentcore-workload" in text
    assert "cgroup OOM killer" in text
    assert "Confidence: high" in text
    assert "[get_container_restart_info] reason OOMKilled, exit 137" in text
    assert "Missing evidence: none" in text
    assert "No remediation was executed." in text


def test_format_report_flags_missing_evidence():
    report = dict(REPORT, missing_evidence=["get_memory_metrics: no datapoints"])
    text = _mod.format_report(INCIDENT, report)
    assert "Missing evidence: get_memory_metrics: no datapoints" in text


def test_format_report_warns_if_remediation_not_false():
    """A report claiming remediation ran must be visibly flagged, not rendered
    as if it were a normal read-only investigation."""
    text = _mod.format_report(INCIDENT, dict(REPORT, remediation_executed=True))
    assert "WARNING" in text


def test_publish_failure_does_not_lose_the_report(monkeypatch):
    """The report is already logged, so a failed publish is degraded delivery
    rather than a lost investigation."""
    monkeypatch.setattr(_mod, "invoke_agent", lambda i: {"response": REPORT})

    def boom(incident, report):
        raise RuntimeError("sns unavailable")

    monkeypatch.setattr(_mod, "publish_report", boom)
    result = handler(EVENT, None)
    assert result["ok"] is True
    assert result["report"]["confidence"] == "high"


def test_slack_payload_uses_custom_schema():
    """Chatbot drops plain text silently -- the payload must use its schema."""
    payload = _mod.slack_payload(INCIDENT, REPORT)
    assert payload["version"] == "1.0"
    assert payload["source"] == "custom"
    assert "incident-demo/aiops-agentcore-workload" in payload["content"]["title"]
    assert "No remediation was executed." in payload["content"]["description"]
