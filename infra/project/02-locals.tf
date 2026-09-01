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
  # website
  # ##############################
  site_domain      = "aiops.arguswatcher.net"
  site_cert_domain = "*.arguswatcher.net"
  site_root        = "${path.module}/../../web"

  # The site lives under this prefix of the existing project bucket.
  site_prefix    = "web"
  site_origin_id = "s3-${local.prefix_name}-site"

  # content types for the objects uploaded to the site bucket
  site_mime_types = {
    css   = "text/css"
    gif   = "image/gif"
    html  = "text/html"
    ico   = "image/x-icon"
    jpg   = "image/jpeg"
    jpeg  = "image/jpeg"
    js    = "application/javascript"
    json  = "application/json"
    png   = "image/png"
    svg   = "image/svg+xml"
    txt   = "text/plain"
    webp  = "image/webp"
    woff  = "font/woff"
    woff2 = "font/woff2"
  }

  # ##############################
  # GitHub
  # ##############################
  github_repo       = "simonangel-fong/aiops-agentcore"
  github_owner_id   = "64545430"
  github_repo_id    = "1351804212"
  github_sub_prefix = "repo:simonangel-fong@${local.github_owner_id}/aiops-agentcore@${local.github_repo_id}"
}
