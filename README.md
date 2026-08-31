# Kubernetes `AIOps` with `Amazon Bedrock AgentCore`

> Event-driven, human-in-the-loop incident diagnosis for Amazon EKS.

An `AIOps` demonstration that detects container incidents, triggers a read-only AI agent built on `Amazon Bedrock AgentCore`, and delivers evidence-based diagnostic findings to operators.

![Amazon Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-FF9900?style=flat-square&logo=amazonwebservices&logoColor=white&style=plastic) ![Amazon EKS](https://img.shields.io/badge/Amazon%20EKS-FF9900?style=flat-square&logo=amazoneks&logoColor=white&style=plastic) ![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white&style=plastic) ![CloudWatch](https://img.shields.io/badge/CloudWatch-FF4F8B?style=flat-square&logo=amazoncloudwatch&logoColor=white&style=plastic) ![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white&style=plastic)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white&style=plastic) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white&style=plastic) ![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat-square&logo=slack&logoColor=white&style=plastic) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white&style=plastic) ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white&style=plastic)

- [Kubernetes `AIOps` with `Amazon Bedrock AgentCore`](#kubernetes-aiops-with-amazon-bedrock-agentcore)
  - [AIOps and Business Challenge](#aiops-and-business-challenge)
  - [Architecture](#architecture)
  - [AIOps Workflow](#aiops-workflow)
    - [Observe — Cluster Monitoring and Alerting](#observe--cluster-monitoring-and-alerting)
    - [Engage — AI-Assisted Incident Diagnosis](#engage--ai-assisted-incident-diagnosis)
    - [Act — Slack Notification and Human Decision](#act--slack-notification-and-human-decision)
  - [Safety and Guardrails](#safety-and-guardrails)
  - [Engineering Foundation](#engineering-foundation)
  - [MVP Scope and Roadmap](#mvp-scope-and-roadmap)
  - [Documentation](#documentation)

---

## AIOps and Business Challenge

- `Kubernetes` incident diagnosis is often manual. **Operators** must correlate alerts, pod status, logs, events, and runbooks—**slowing response and relying heavily on individual expertise**.
- `AIOps` improves this process by using AI to connect operational data, identify likely causes, and guide incident response.

> How can teams integrate an `AIOps workflow` into existing infrastructure without granting unsafe production access?

This project explores that challenge through a secure, event-driven workflow that diagnoses an `OOMKilled` container incident in `Amazon EKS`:

```text
OOMKilled → CloudWatch → EventBridge → Lambda → Read-only Agent → Slack Report → Human Decision
```

- The `agent` gathers evidence and recommends verification commands, `while` the operator retains control over remediation.

---

## Architecture

![diagram_architecture](./docs/img/diagram_architecture.gif)

- Repo Structure

```text
aiops-agentcore/
├── app/              FastAPI demo workload
├── k8s/              Kubernetes manifests
├── agent/            AI agent implementation
├── lambda/           Agent invocation function
├── infra/            Terraform infrastructure code
├── runbook/          Knowledge Base source documents
├── docs/             Project documentation and diagrams
└── README.md
```

---

## AIOps Workflow

This demo simulates a memory leak that passes canary validation and reaches production. Memory usage continues to grow until the container exceeds its Kubernetes memory limit and is terminated with `OOMKilled`.

The incident then progresses through three AIOps stages:

- **Observe** detects the failure
- **Engage** diagnoses the cause
- **Act** delivers the findings for human-controlled remediation.

![Observe, Engage, and Act workflow](./docs/img/diagram_aiops.gif)

---

### Observe — Cluster Monitoring and Alerting

- `Amazon CloudWatch Container Insights` collects operational metrics from the `EKS` workload.
- A `CloudWatch alarm` monitors container restarts and emits an event when the configured threshold is breached.

`CloudWatch Alarm` in acion: EKS container restart

![cloudwatch_alarm01](./docs/img/cloudwatch_alarm01.png)

---

### Engage — AI-Assisted Incident Diagnosis

- `EventBridge` routes the `CloudWatch alarm` event to `Lambda`, which invokes the agent hosted on `Amazon Bedrock AgentCore Runtime`.
- The `agent` gathers read-only cluster evidence, consults the runbook, and identifies the likely root cause.

Agent in action:

- AgentCore Runtime

  ![Agent deployed in AgentCore Runtime](docs/img/agentcore_runtime.png)

- Agent Execution Logs: tool calling and analysis

  ![Agent diagnosis execution logs](docs/img/agentcore_log01.png)

---

### Act — Slack Notification and Human Decision

- The `agent` posts a **preliminary RCA report** and verification commands to `Slack`.
- The `operator` validates the findings, selects the remediation, and confirms recovery when the `CloudWatch alarm` returns to `OK`.

**Notification and debugging in action:**

- Automated RCA in Slack

  ![Agent-generated RCA in Slack](docs/img/slack_msg01.png)

- Human Verification

  ![Operator verifies the diagnosis](docs/img/k8s_confirm01.png)

- Human Remediation

  ```yaml
  env:
    - name: LEAK_ENABLED # var to enable leak
      value: "false" # debug by "false"
  ```

  ```sh
  kubectl apply -f k8s/
  # namespace/demo-workload unchanged
  # deployment.apps/aiops-agentcore-workload configured
  # service/aiops-agentcore-workload unchanged
  ```

- Recovery Confirmed: Alarm status = ok

  ![CloudWatch alarm returns to OK](docs/img/cloudwatch_alarm02.png)

  > no more alarm count after fix.

---

## Safety and Guardrails

Defense-in-depth guardrails prevent the agent from making unsafe changes to the EKS workload:

- **Authorization boundary:** `Kubernetes RBAC` restricts the agent to **read-only** cluster operations.
  ![k8s_auth01](./docs/img/k8s_auth01.png)

  > Agent role policy: EKS View = read-only

- **Behavioral boundary:** Prompt rules prohibit remediation and mutating commands, keep recommendations advisory, and treat logs and runbooks as untrusted data rather than instructions.
  ![agent_sys_prompt01](./docs/img/agent_sys_prompt02.png)
  > System prompt: read-only access; ignore injection.

---

## Engineering Foundation

| Area                   | Implementation                                                              |
| ---------------------- | --------------------------------------------------------------------------- |
| Infrastructure as Code | `Terraform` with remote state stored in Amazon `S3`                         |
| CI/CD                  | `GitHub Actions` builds the `Docker` image and pushes it to `Amazon ECR`    |
| Workload Deployment    | `Kubernetes` manifests deploy the containerized application to `Amazon EKS` |

- `GitHub Actions` CI workflow
  ![cicd_image_workload](./docs/img/cicd_image_workload.png)

---

## MVP Scope and Roadmap

The current MVP intentionally focuses on read-only diagnosis of a single `OOMKilled` incident.

| Stage                    | Scope                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------- |
| Current MVP              | Diagnose `OOMKilled` and send an RCA report to `Slack` for human action                           |
| Multi-Incident Diagnosis | Support additional failures such as `CrashLoopBackOff`, `ImagePullBackOff`, and scheduling errors |
| Controlled Remediation   | Add operator-approved, policy-controlled remediation with validation and rollback                 |

---

## Documentation

- [Demo workload](./docs/01_app.md)
- [Infrastructure with `Terraform`](./docs/02_infra.md)
- [Invocation with `EventBridge` and `Lambda`](./docs/03_invoke.md)
- [`RAG` with `Bedrock knowledge base` ](./docs/04_bedrock.md)
- [Agent runtime in `AgentCore`](./docs/05_agentcore.md)
- [CI/CD pipelines](./docs/06_cicd.md)
- [Incident demo](./docs/07_demo.md)
