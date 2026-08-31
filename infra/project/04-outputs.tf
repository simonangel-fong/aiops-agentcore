# output.tf

output "project_bucket" {
  description = "S3 bucket for the cluster module's Terraform state"
  value       = aws_s3_bucket.aiops_argentcore.id
}

output "ecr_repo_workload_url" {
  description = "Push target for the app image"
  value       = aws_ecr_repository.this["workload"].repository_url
}

output "ecr_repo_trigger_url" {
  description = "Push target for the Lambda trigger image"
  value       = aws_ecr_repository.this["trigger"].repository_url
}

output "ecr_repo_agent_url" {
  description = "Push target for the agent image"
  value       = aws_ecr_repository.this["agent"].repository_url
}

output "github_oidc_role_arn" {
  description = "Set as the AWS_ROLE_ARN_GH_OIDC repository variable in GitHub"
  value       = aws_iam_role.github_ecr_push.arn
}
