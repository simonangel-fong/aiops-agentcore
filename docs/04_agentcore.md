# AIOps-AgentCore: Agent with `Amazon AgentCore`

[Back](../README.md)

- [AIOps-AgentCore: Agent with `Amazon AgentCore`](#aiops-agentcore-agent-with-amazon-agentcore)
  - [Agent](#agent)
    - [Agent image](#agent-image)
    - [AgentCore deploy](#agentcore-deploy)
    - [Test runtime](#test-runtime)
  - [Bedrock knowledge base](#bedrock-knowledge-base)
- [Bedrock Knowledge Base](#bedrock-knowledge-base-1)

---

## Agent

- paths

```
GET  /ping        -> 200 {"status": "Healthy"}
POST /invocations -> 200 status=success, root_cause=OOM killer, 6 evidence items
```

- Model
  - `global.anthropic.claude-haiku-4-5-20251001-v1:0`
  - Cost: **~$0.029 per report** (20.7k in / 1.6k out at Haiku 4.5 rates).

- Run locally

```sh
pip install -r agent/requirements.txt
pytest agent/
# 7 passed

cd agent/src
KNOWLEDGE_BASE_ID=DR2GI2F7DE AWS_REGION=ca-central-1 \
  ../../.venv/Scripts/python.exe agent.py incident-demo kube-agent-app
```

---

### Agent image

```sh
terraform -chdir=infra/project output -raw ecr_repo_agent_url
# 099139718958.dkr.ecr.ca-central-1.amazonaws.com/aiops-agentcore-agent

# run QEMU: agent build arm64; but windows in amd64
docker run --privileged --rm tonistiigi/binfmt --install arm64

# build and push
docker buildx build --platform linux/arm64 -t "099139718958.dkr.ecr.ca-central-1.amazonaws.com/aiops-agentcore-agent:latest" --push agent/
```

---

### AgentCore deploy

```sh
terraform -chdir=infra/cluster fmt && terraform -chdir=infra/cluster validate
terraform -chdir=infra/cluster apply -auto-approve
```

---

### Test runtime

```sh
terraform -chdir=infra/cluster output -raw agent_runtime_arn
# arn:aws:bedrock-agentcore:ca-central-1:099139718958:runtime/aiops_agentcore_cluster_agent-U0qT9XACgj

# test runtime
aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn "arn:aws:bedrock-agentcore:ca-central-1:099139718958:runtime/aiops_agentcore_cluster_agent-U0qT9XACgj" --region ca-central-1 --content-type application/json --payload fileb://agent/runtime_test/payload.json agent/runtime_test/out.json
# {
#     "runtimeSessionId": "8cb3dbf6-69ac-4e34-9b97-7a0eedcdd751",
#     "contentType": "application/json",
#     "statusCode": 200
# }
```

---

## Bedrock knowledge base

# Bedrock Knowledge Base

```sh
# get kb
terraform -chdir=infra/cluster output -raw knowledge_base_id
# DR2GI2F7DE

# get kb source
terraform -chdir=infra/cluster output -raw knowledge_base_data_source_id
# 6SPEYBHNGY

# ingest kb from data source
aws bedrock-agent start-ingestion-job --knowledge-base-id "DR2GI2F7DE" --data-source-id "6SPEYBHNGY" --region ca-central-1
# {
#     "ingestionJob": {
#         "knowledgeBaseId": "DR2GI2F7DE",
#         "dataSourceId": "6SPEYBHNGY",
#         "ingestionJobId": "SMSZ8GIZ5E",
#         "status": "STARTING",
#         "statistics": {
#             "numberOfDocumentsScanned": 0,
#             "numberOfMetadataDocumentsScanned": 0,
#             "numberOfNewDocumentsIndexed": 0,
#             "numberOfModifiedDocumentsIndexed": 0,
#             "numberOfMetadataDocumentsModified": 0,
#             "numberOfDocumentsDeleted": 0,
#             "numberOfDocumentsFailed": 0
#         },
#         "startedAt": "2026-08-29T21:16:07.934780+00:00",
#         "updatedAt": "2026-08-29T21:16:07.934780+00:00"
#     }
# }


# confirm injest job complete
aws bedrock-agent get-ingestion-job --knowledge-base-id "DR2GI2F7DE" --data-source-id "6SPEYBHNGY" --ingestion-job-id "SMSZ8GIZ5E" --region ca-central-1 --query 'ingestionJob.[status,statistics.numberOfNewDocumentsIndexed,statistics.numberOfDocumentsFailed]' --output text
# COMPLETE       1       0

# retrieve
aws bedrock-agent-runtime retrieve --knowledge-base-id "DR2GI2F7DE" --region ca-central-1 --retrieval-query '{"text":"container exit code 137"}' --query 'retrievalResults[].[score]' --output text
# 0.8331561982631683
```
