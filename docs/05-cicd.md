# AIOps-AgentCore: CD/CD

[Back](../README.md)

- [AIOps-AgentCore: CD/CD](#aiops-agentcore-cdcd)
  - [GitHub config](#github-config)
  - [Pipeline](#pipeline)

---

## GitHub config

- Variables

| Variable              | descripion                   |
| --------------------- | ---------------------------- |
| AWS_ROLE_ARN_ECR_OIDC | OIDC role for GitHub Actions |

```sh
terraform -chdir=infra/project output -raw github_oidc_role_arn
gh variable set AWS_ROLE_ARN_ECR_OIDC -b "arn:aws:iam::099139718958:role/aiops-agentcore-project-github-ecr-push"
# ✓ Created variable AWS_ROLE_ARN_ECR_OIDC for simonangel-fong/aiops-agentcore


```

---

## Pipeline

| Pipeline                | Description                         |
| ----------------------- | ----------------------------------- |
| build-push-ecr-workload | build and push demo workload image  |
| terraform-apply-project | apply project level terraform codes |

```sh
gh workflow run build-push-ecr-workload
```

![cicd_image_workload](./img/cicd_image_workload.png)
