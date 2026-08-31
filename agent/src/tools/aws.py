"""Tools to interact with AWS resouces."""

import os
from datetime import datetime, timedelta, timezone

import boto3

# get env var
REGION = os.environ.get("AWS_REGION", "ca-central-1")
CLUSTER = os.environ.get("CLUSTER_NAME", "aiops-agentcore")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")


def get_memory_metrics(namespace: str, pod: str, minutes: int = 30) -> dict:
    """
    Get pod memory utilisation against its limit from Container Insights.
    Default: last 30min metrics
    """

    cw = boto3.client("cloudwatch", region_name=REGION)
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    # get metric
    resp = cw.get_metric_statistics(
        Namespace="ContainerInsights",
        MetricName="pod_memory_utilization_over_pod_limit",
        Dimensions=[
            {"Name": "PodName", "Value": pod},
            {"Name": "Namespace", "Value": namespace},
            {"Name": "ClusterName", "Value": CLUSTER},
        ],
        StartTime=start, EndTime=end,
        Period=60, Statistics=["Maximum"],
    )

    # sort metrics
    points = sorted(resp.get("Datapoints", []), key=lambda d: d["Timestamp"])
    # if no metrics
    if not points:
        return {
            "available": False,
            "reason": f"no datapoints in the last {minutes} minutes "
                      "(Container Insights lags 1-3 minutes behind an incident)",
        }

    return {
        "available": True,
        "metric": "pod_memory_utilization_over_pod_limit",
        "unit": "percent of limit",
        "datapoints": [
            {"timestamp": p["Timestamp"].isoformat(), "max": round(p["Maximum"], 1)}
            for p in points
        ],
        "peak": round(max(p["Maximum"] for p in points), 1),
    }


def search_runbook(query: str, max_results: int = 3) -> dict:
    """Retrieve passages from the OOM runbook."""
    # when kb not available
    if not KNOWLEDGE_BASE_ID:
        return {"available": False, "reason": "KNOWLEDGE_BASE_ID is not configured"}

    br = boto3.client("bedrock-agent-runtime", region_name=REGION)

    # get reference in kb
    resp = br.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": max_results}
        },
    )

    results = resp.get("retrievalResults", [])
    # when no match
    if not results:
        return {"available": False, "query": query, "reason": "no matching passages"}

    return {
        "available": True,
        "query": query,
        "passages": [{
            "score": round(r.get("score", 0), 3),
            "source": r.get("location", {}).get("s3Location", {}).get("uri"),
            "text": r["content"]["text"],
        } for r in results],
    }
