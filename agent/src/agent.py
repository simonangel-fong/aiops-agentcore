"""Strands incident triage agent."""

import json
import os
import re

from strands import Agent, tool
from strands.models import BedrockModel

from audit import audited
from prompt import SYSTEM_PROMPT
from tools import (
    get_container_restart_info,
    get_kubernetes_events,
    get_memory_metrics,
    get_pod_logs,
    get_pod_status,
    get_resource_limits,
    search_runbook,
)

# env var
MODEL_ID = os.environ.get(
    "AGENT_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0"
) # model
REGION = os.environ.get("AWS_REGION", "ca-central-1")

TOOLS = [
    get_pod_status,
    get_container_restart_info,
    get_pod_logs,
    get_kubernetes_events,
    get_memory_metrics,
    get_resource_limits,
    search_runbook,
]


def build_agent() -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[tool(audited(f)) for f in TOOLS],
    )


def _extract_report(text: str) -> dict:
    """Pull the JSON report out of the model's final message."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {"error": "no JSON report in response", "raw": text[:500]}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return {"error": f"malformed JSON report: {exc}", "raw": text[:500]}


def investigate(cluster: str, namespace: str, pod: str) -> dict:
    """Run one investigation and return the structured report."""
    agent = build_agent()
    result = agent(
        f"Container in pod '{pod}' (namespace '{namespace}', cluster '{cluster}') "
        "restarted. Investigate and produce the report."
    )
    report = _extract_report(str(result))

    usage = getattr(result, "metrics", None)
    if usage is not None:
        acc = getattr(usage, "accumulated_usage", None) or {}
        report["_usage"] = {
            "input_tokens": acc.get("inputTokens"),
            "output_tokens": acc.get("outputTokens"),
        }
    return report


if __name__ == "__main__":
    import sys

    ns = sys.argv[1] if len(sys.argv) > 1 else "incident-demo"
    pd = sys.argv[2] if len(sys.argv) > 2 else "aiops-agentcore-workload"
    print(json.dumps(investigate("aiops-agentcore", ns, pd), indent=2))
