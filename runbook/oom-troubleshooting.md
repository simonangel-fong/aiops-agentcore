# Runbook: Container Restart — OOMKilled

Scope: a container in an EKS pod restarted and the cause must be established
from read-only evidence. This runbook is advisory. It never authorises
remediation; a human decides what to change.

## 1. Confirming an OOM kill

A container terminated by the kernel's cgroup OOM killer shows **both** of the
following in the pod's previous container state:

- `reason: OOMKilled`
- `exitCode: 137`

`reason` is the decisive field. Check it in `lastState.terminated` for the
container that restarted, not in the current running state.

If `reason` is `OOMKilled`, the container exceeded its memory limit. This is
sufficient to confirm the root cause on its own; supporting evidence
strengthens the report but is not required for the diagnosis.

## 2. Exit code 137 does not by itself prove OOM

Exit code 137 means the process received SIGKILL (128 + 9). Several causes
produce it:

| Cause                     | `reason`              | Distinguishing evidence                                       |
| ------------------------- | --------------------- | ------------------------------------------------------------- |
| Cgroup OOM kill           | `OOMKilled`           | Memory at or near the limit before termination                |
| Liveness probe failure    | `Error`               | `Unhealthy` and `Killing` events; memory well below the limit |
| Manual or controller kill | `Error`               | `Killing` event without a probe failure                       |
| Node pressure eviction    | `Evicted` (pod-level) | Node condition `MemoryPressure`, pod status `Failed`          |

**Never diagnose OOM from exit code 137 alone.** If `reason` is `Error` and the
events show a failed liveness probe, the restart is probe-related, not an OOM.

## 3. Distinguishing from an application exit

A container that exits on its own has a non-137 exit code — commonly `1` for an
unhandled exception. `reason` is `Error` and there is no `Killing` event. Look
for a stack trace or fatal log line at the end of the previous container's logs.

## 4. Evidence to gather

In order of diagnostic value:

1. **Termination state** — `reason`, `exitCode`, `startedAt`, `finishedAt`
   from the previous container state. Decisive.
2. **Previous container logs** — the final lines before termination. An OOM
   kill is abrupt: expect no shutdown message and no stack trace. Logs from
   this application are one JSON object per line with `timestamp`, `level`,
   `event`, `allocated_mb`, `rss_mb`.
3. **Configured limits** — `resources.limits.memory`. Compare against the last
   observed memory figure.
4. **Memory metrics** — `pod_memory_utilization_over_pod_limit` from Container
   Insights, over the minutes preceding termination. A climb toward 100%
   corroborates an OOM.
5. **Kubernetes events** — note that a cgroup OOM kill produces **no event
   naming OOMKilled**. Absence of an OOM event is expected and is not evidence
   against an OOM diagnosis. Events matter mainly for ruling out probe failures.

## 5. When evidence is missing

Container Insights metrics lag roughly one to three minutes behind an incident
and may be unavailable when an investigation runs promptly. Previous-container
logs are lost if the container has restarted more than once since.

If a data source is unavailable, say so explicitly in the report, list which
source was missing, and lower the stated confidence. Do not infer a value that
was not retrieved, and do not treat an absent source as agreement.

A diagnosis resting on `reason: OOMKilled` alone remains valid — report it with
the caveat that corroborating metrics were unavailable.

## 6. Verification commands for the administrator

```
kubectl describe pod -n <namespace> <pod>
kubectl logs -n <namespace> <pod> --previous | tail -20
kubectl get events -n <namespace> --sort-by=.lastTimestamp
kubectl get deploy -n <namespace> <deployment> -o jsonpath='{.spec.template.spec.containers[0].resources}'
```

## 7. Remediation options — advisory only

Do not apply these. Present them for a human to choose:

- **Raise `limits.memory`** if the workload's legitimate working set exceeds
  the current limit. Confirm the steady-state figure first; raising a limit to
  mask a leak only delays the failure.
- **Fix the application leak** if memory grows without bound. Growth that never
  plateaus indicates retained references, not an undersized limit.
- **Set `requests.memory` closer to actual usage** so the scheduler places the
  pod on a node with sufficient headroom.

Raising a limit and fixing a leak are different responses to different
evidence. Recommend the one the memory profile supports; if the profile is
unavailable, say which evidence would decide it.
