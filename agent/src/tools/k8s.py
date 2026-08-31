"""Tools to interact with k8s."""

import base64
import os
import re
import tempfile

import boto3
from botocore.signers import RequestSigner
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# env var
REGION = os.environ.get("AWS_REGION", "ca-central-1")
CLUSTER = os.environ.get("CLUSTER_NAME", "aiops-agentcore")

# STS presigned-URL token, the same scheme `aws eks get-token` uses.
_TOKEN_TTL = 60
_STS_HEADER = "x-k8s-aws-id"


def _eks_token(cluster: str, session) -> str:
    """Presign an STS GetCallerIdentity URL and encode it as a k8s bearer token."""
    sts = session.client("sts", region_name=REGION)
    signer = RequestSigner(
        sts.meta.service_model.service_id,
        REGION,
        "sts",
        "v4",
        session.get_credentials(),
        session.events,
    )
    url = signer.generate_presigned_url(
        {
            "method": "GET",
            "url": (
                f"https://sts.{REGION}.amazonaws.com/"
                "?Action=GetCallerIdentity&Version=2011-06-15"
            ),
            "body": {},
            "headers": {_STS_HEADER: cluster},
            "context": {},
        },
        region_name=REGION,
        expires_in=_TOKEN_TTL,
        operation_name="",
    )
    encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    return f"k8s-aws-v1.{encoded}"


def _eks_api():
    """Build a client from the EKS API using the execution role's IAM identity.
    """
    session = boto3.Session()
    described = session.client("eks", region_name=REGION).describe_cluster(
        name=CLUSTER
    )["cluster"]

    cfg = client.Configuration()
    cfg.host = described["endpoint"]
    cfg.api_key = {"authorization": "Bearer " + _eks_token(CLUSTER, session)}

    # The CA is base64 PEM; the client needs it on disk.
    ca = base64.b64decode(described["certificateAuthority"]["data"])
    fd, ca_path = tempfile.mkstemp(suffix=".pem")
    with os.fdopen(fd, "wb") as fh:
        fh.write(ca)
    cfg.ssl_ca_cert = ca_path

    return client.CoreV1Api(client.ApiClient(cfg))


def _api():
    """In-cluster config, else local kubeconfig, else the EKS API directly."""
    try:
        config.load_incluster_config()
        return client.CoreV1Api()
    except config.ConfigException:
        pass
    try:
        config.load_kube_config()
        return client.CoreV1Api()
    except Exception:
        # No kubeconfig on disk: running somewhere like AgentCore.
        return _eks_api()


def _resolve_pod(api, namespace, pod):
    """Accept either a full pod name or a deployment-level prefix.    """
    try:
        return api.read_namespaced_pod(name=pod, namespace=namespace)
    except ApiException as exc:
        if exc.status != 404:
            raise
    pods = api.list_namespaced_pod(namespace=namespace).items
    matches = [p for p in pods if p.metadata.name.startswith(pod)]
    if not matches:
        return None
    # Most recently started first.
    matches.sort(key=lambda p: p.status.start_time or 0, reverse=True)
    return matches[0]


def get_pod_status(namespace: str, pod: str) -> dict:
    """Get pod phase, restart count and per-container readiness."""
    api = _api()
    p = _resolve_pod(api, namespace, pod)
    if p is None:
        return {"available": False, "reason": f"no pod matching '{pod}' in {namespace}"}

    containers = []
    for cs in p.status.container_statuses or []:
        containers.append({
            "name": cs.name,
            "ready": cs.ready,
            "restart_count": cs.restart_count,
            "state": next(iter([k for k, v in (cs.state.to_dict() or {}).items() if v]), None),
        })

    return {
        "available": True,
        "pod": p.metadata.name,
        "phase": p.status.phase,
        "start_time": str(p.status.start_time),
        "containers": containers,
    }


def get_container_restart_info(namespace: str, pod: str, container: str = None) -> dict:
    """Last termination reason and exit code — the decisive OOM evidence."""
    api = _api()
    p = _resolve_pod(api, namespace, pod)
    if p is None:
        return {"available": False, "reason": f"no pod matching '{pod}' in {namespace}"}

    for cs in p.status.container_statuses or []:
        if container and cs.name != container:
            continue
        last = cs.last_state.terminated if cs.last_state else None
        if last is None:
            return {
                "available": False,
                "pod": p.metadata.name,
                "container": cs.name,
                "restart_count": cs.restart_count,
                "reason": "container has no previous termination state",
            }
        return {
            "available": True,
            "pod": p.metadata.name,
            "container": cs.name,
            "restart_count": cs.restart_count,
            "termination_reason": last.reason,
            "exit_code": last.exit_code,
            "started_at": str(last.started_at),
            "finished_at": str(last.finished_at),
        }

    return {"available": False, "reason": "no matching container"}


def get_pod_logs(namespace: str, pod: str, previous: bool = True, lines: int = 40) -> dict:
    """Logs from the current or previous container.

    ``previous=True`` is the important case: it returns the killed container's
    output, which is where the memory growth is visible.
    """
    api = _api()
    p = _resolve_pod(api, namespace, pod)
    if p is None:
        return {"available": False, "reason": f"no pod matching '{pod}' in {namespace}"}

    try:
        raw = api.read_namespaced_pod_log(
            name=p.metadata.name, namespace=namespace,
            previous=previous, tail_lines=lines,
        )
    except ApiException as exc:
        return {
            "available": False,
            "pod": p.metadata.name,
            "previous": previous,
            "reason": f"logs unavailable: {exc.reason}",
        }

    return {
        "available": True,
        "pod": p.metadata.name,
        "previous": previous,
        "lines": [l for l in raw.splitlines() if l.strip()],
    }


def get_kubernetes_events(namespace: str, pod: str, limit: int = 15) -> dict:
    """Recent events for the pod.

    Note for the agent: a cgroup OOM kill produces no event naming OOMKilled.
    Events are useful mainly for ruling out probe failures.
    """
    api = _api()
    p = _resolve_pod(api, namespace, pod)
    name = p.metadata.name if p else pod

    evs = api.list_namespaced_event(
        namespace=namespace,
        field_selector=f"involvedObject.name={name}",
    ).items
    if not evs:
        return {"available": False, "pod": name, "reason": "no events found for this pod"}

    evs.sort(key=lambda e: e.last_timestamp or e.event_time or 0, reverse=True)
    return {
        "available": True,
        "pod": name,
        "events": [{
            "type": e.type,
            "reason": e.reason,
            "message": e.message,
            "count": e.count,
            "last_timestamp": str(e.last_timestamp),
        } for e in evs[:limit]],
    }


def get_resource_limits(namespace: str, pod: str) -> dict:
    """Configured memory/cpu requests and limits."""
    api = _api()
    p = _resolve_pod(api, namespace, pod)
    if p is None:
        return {"available": False, "reason": f"no pod matching '{pod}' in {namespace}"}

    return {
        "available": True,
        "pod": p.metadata.name,
        "containers": [{
            "name": c.name,
            "requests": (c.resources.requests or {}) if c.resources else {},
            "limits": (c.resources.limits or {}) if c.resources else {},
        } for c in p.spec.containers],
    }
