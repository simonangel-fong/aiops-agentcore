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

output "site_url" {
  description = "Public URL of the project website"
  value       = "https://${local.site_domain}"
}

output "site_bucket_prefix" {
  description = "Bucket and prefix holding the website content"
  value       = "s3://${aws_s3_bucket.aiops_argentcore.id}/${local.site_prefix}/"
}

output "site_cloudfront_domain" {
  description = "CloudFront domain the Cloudflare CNAME points at"
  value       = aws_cloudfront_distribution.site.domain_name
}

output "site_cloudfront_distribution_id" {
  description = "Distribution id, for cache invalidation after a content update"
  value       = aws_cloudfront_distribution.site.id
}
