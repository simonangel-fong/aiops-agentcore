# AIOps-AgentCore: Invocation with `EventBridge` and `Lambda`

[Back](../README.md)

- [AIOps-AgentCore: Invocation with `EventBridge` and `Lambda`](#aiops-agentcore-invocation-with-eventbridge-and-lambda)
  - [Cloudwatch alarm](#cloudwatch-alarm)
  - [Lambda function](#lambda-function)
    - [Lambda image](#lambda-image)
    - [Lambda deploy](#lambda-deploy)

---

## Cloudwatch alarm

```sh
# confirm container insight is enabled
aws cloudwatch list-metrics --namespace ContainerInsights --region ca-central-1 --dimensions Name=ClusterName,Value=aiops-agentcore

# confirm alarm
aws cloudwatch describe-alarms --alarm-names "aiops-agentcore-cluster-container-restart" --region ca-central-1 --query 'MetricAlarms[0].Dimensions' --output table
# ---------------------------------------------
# |              DescribeAlarms               |
# +--------------+----------------------------+
# |     Name     |           Value            |
# +--------------+----------------------------+
# |  PodName     |  aiops-agentcore-workload  |
# |  Namespace   |  demo-workload             |
# |  ClusterName |  aiops-agentcore           |
# +--------------+----------------------------+
```

![cloudwatch_alarm01](./img/cloudwatch_alarm01.png)

---

## Lambda function

### Lambda image

```sh
pip install -r lambda/trigger/requirements.txt

pytest lambda/trigger
# 9 passed in 0.31s

terraform -chdir=infra/project output -raw ecr_repo_trigger_url
# 099139718958.dkr.ecr.ca-central-1.amazonaws.com/aiops-agentcore-trigger

# login
aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin "099139718958.dkr.ecr.ca-central-1.amazonaws.com"
# Login Succeeded

# build and push
docker buildx build --platform linux/amd64 --provenance=false --sbom=false --output type=image,oci-mediatypes=false,push=true -t "099139718958.dkr.ecr.ca-central-1.amazonaws.com/aiops-agentcore-trigger:latest" lambda/trigger
```

---

### Lambda deploy

```sh
terraform -chdir=infra/cluster fmt && terraform -chdir=infra/cluster validate
terraform -chdir=infra/cluster apply -auto-approve

# confirm
kubectl rollout restart deploy/aiops-agentcore-workload -n demo-workload
# deployment.apps/aiops-agentcore-workload restarted

# confirm in log
aws logs tail /aws/lambda/aiops-agentcore-cluster-trigger --follow --region ca-central-1
# incident_detected: {...}
# incident_report:   {"root_cause": "...", "confidence": "high", ...}
```
