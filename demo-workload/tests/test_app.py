import importlib
import json
import sys
import time

import pytest
from fastapi.testclient import TestClient

REQUIRED_FIELDS = {"timestamp", "level", "event", "allocated_mb", "rss_mb"}


@pytest.fixture
def app_with(monkeypatch):
    """Import src.main with the given env vars applied."""
    def _make(**env):
        for key, value in env.items():
            monkeypatch.setenv(key, str(value))
        sys.modules.pop("src.main", None)
        return importlib.import_module("src.main")
    return _make


def logs(capsys):
    return [json.loads(l) for l in capsys.readouterr().out.splitlines() if l.strip()]


def test_endpoints(app_with):
    main = app_with(LEAK_ENABLED="false")
    with TestClient(main.app) as client:
        assert client.get("/").json() == {"service": "aiops-agentcore-workload", "status": "ok"}
        assert client.get("/healthz").json() == {"status": "healthy"}
        assert client.get("/status").json()["rss_mb"] > 0


def test_leak_grows(app_with):
    """Allocation and RSS both climb — proves the pages are really committed."""
    main = app_with(LEAK_START_SECONDS=0, LEAK_MB_PER_TICK=4, LEAK_INTERVAL_SECONDS=1)
    with TestClient(main.app) as client:
        first = client.get("/status").json()
        time.sleep(3)
        later = client.get("/status").json()

    assert later["allocated_mb"] > first["allocated_mb"]
    assert later["rss_mb"] > first["rss_mb"]


def test_leak_disabled(app_with):
    """The Phase 5 control case: same image, no leak."""
    main = app_with(LEAK_ENABLED="false", LEAK_START_SECONDS=0)
    with TestClient(main.app) as client:
        time.sleep(2)
        assert client.get("/status").json()["allocated_mb"] == 0


def test_leak_start_delay(app_with):
    main = app_with(LEAK_START_SECONDS=5, LEAK_MB_PER_TICK=4)
    with TestClient(main.app) as client:
        time.sleep(2)
        assert client.get("/status").json()["allocated_mb"] == 0


def test_log_contract(app_with, capsys):
    """Guards the fields Phase 3's get_pod_logs depends on."""
    main = app_with(LEAK_START_SECONDS=0, LEAK_MB_PER_TICK=4, LEAK_INTERVAL_SECONDS=1)
    with TestClient(main.app) as client:
        time.sleep(3)
        client.get("/status")

    records = logs(capsys)
    for record in records:
        assert not REQUIRED_FIELDS - record.keys(), f"missing fields: {record}"

    events = [r["event"] for r in records]
    assert "app_started" in events
    assert "leak_started" in events

    progress = [r["allocated_mb"] for r in records if r["event"] == "leak_progress"]
    assert len(progress) >= 2 and progress == sorted(progress)
