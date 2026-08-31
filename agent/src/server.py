"""AgentCore Runtime HTTP wraper.

The runtime requires POST /invocations and GET /ping on port 8080, bound to
0.0.0.0, in an ARM64 container.
"""

import json
import logging
import os
import sys

from fastapi import FastAPI
from pydantic import BaseModel

from agent import investigate


# log
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))

for _name in ("agent", "agent.audit"):
    _log = logging.getLogger(_name)
    _log.setLevel(logging.INFO)
    _log.handlers.clear()
    _log.addHandler(_handler)
    _log.propagate = False

logger = logging.getLogger("agent")

app = FastAPI()


class Invocation(BaseModel):
    # The Lambda sends the identifiers extracted from the alarm event.
    cluster: str = os.environ.get("CLUSTER_NAME", "aiops-agentcore")
    namespace: str
    pod: str


@app.get("/ping")
async def ping():
    return {"status": "Healthy"}


@app.post("/invocations")
async def invocations(body: Invocation):
    logger.info("investigating %s/%s", body.namespace, body.pod)
    try:
        # call function in agent.py
        report = investigate(body.cluster, body.namespace, body.pod)
    except Exception as exc:  # surface failures as a report, not a 500
        logger.exception("investigation failed")
        return {
            "response": {
                "error": f"investigation failed: {exc}",
                "remediation_executed": False,
            },
            "status": "error",
        }

    logger.info("report: %s", json.dumps(report)[:2000])
    return {"response": report, "status": "success"}
