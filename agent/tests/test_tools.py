"""Tool contract tests.

These run against the live cluster and are skipped when it is unreachable, so
the suite still passes on a laptop with no AWS access.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tools import (  # noqa: E402
    get_container_restart_info,
    get_kubernetes_events,
    get_memory_metrics,
    get_pod_logs,
    get_pod_status,
    get_resource_limits,
    search_runbook,
)

NS = "demo-workload"
POD = "aiops-agentcore-workload"


def _live():
    try:
        return get_pod_status(namespace=NS, pod=POD).get("available") is True
    except Exception:
        return False


live_only = pytest.mark.skipif(not _live(), reason="cluster unreachable")


@live_only
def test_restart_info_reports_oom():
    """The decisive evidence: reason and exit code from the previous state."""
    r = get_container_restart_info(namespace=NS, pod=POD)
    assert r["available"] is True
    assert r["termination_reason"] == "OOMKilled"
    assert r["exit_code"] == 137
    assert r["restart_count"] >= 1


@live_only
def test_resolves_deployment_prefix():
    """The alarm supplies the deployment name, not the restarting pod name."""
    r = get_pod_status(namespace=NS, pod=POD)
    assert r["available"] is True
    assert r["pod"].startswith(POD)
    assert r["pod"] != POD, "should resolve to the full pod name"


@live_only
def test_previous_logs_are_structured():
    r = get_pod_logs(namespace=NS, pod=POD, previous=True)
    assert r["available"] is True
    assert r["lines"], "previous container produced no logs"
    assert r["lines"][-1].startswith("{"), "logs must be the JSON contract"


@live_only
def test_limits_present():
    r = get_resource_limits(namespace=NS, pod=POD)
    assert r["available"] is True
    assert "memory" in r["containers"][0]["limits"]


@live_only
def test_events_available():
    r = get_kubernetes_events(namespace=NS, pod=POD)
    assert r["available"] is True
    assert r["events"]


@live_only
@pytest.mark.skipif(not os.environ.get("KNOWLEDGE_BASE_ID"), reason="KB not configured")
def test_runbook_retrieval():
    r = search_runbook(query="container exit code 137")
    assert r["available"] is True
    assert r["passages"][0]["score"] > 0.5


# --- contract: missing data is reported, never inferred ---------------------

def test_missing_pod_reports_unavailable():
    r = get_pod_status(namespace=NS, pod="no-such-app-xyz")
    assert r["available"] is False
    assert "no pod matching" in r["reason"]


def test_missing_metrics_report_unavailable():
    r = get_memory_metrics(namespace=NS, pod="no-such-app-xyz")
    assert r["available"] is False
    assert r["reason"]
