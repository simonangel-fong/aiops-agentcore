# locals.tf

locals {

  # ##############################
  # metadata
  # ##############################
  project_name = "aiops-agentcore"
  prefix_name  = "${local.project_name}-project"
  default_tags = {
    Project   = local.project_name
    Env       = "project"
    ManagedBy = "Terraform"
  }

  # ##############################
  # aws
  # ##############################
  aws_region = "ca-central-1"

  # ##############################
  # ECR
  # ##############################
  ecr_repo_list = ["workload", "trigger", "agent"]

  # ##############################
  # GitHub
  # ##############################
  github_repo       = "simonangel-fong/aiops-agentcore"
  github_owner_id   = "64545430"
  github_repo_id    = "1351804212"
  github_sub_prefix = "repo:simonangel-fong@${local.github_owner_id}/aiops-agentcore@${local.github_repo_id}"
}
