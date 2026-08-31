# locals.tf

locals {
  # ##############################
  # metadata
  # ##############################
  project_name = "aiops-agentcore"
  prefix_name  = "${local.project_name}-cluster"
  default_tags = {
    Project   = local.project_name
    Env       = "cluster"
    ManagedBy = "Terraform"
  }

  # ##############################
  # aws
  # ##############################
  aws_region = "ca-central-1"

  # ##############################
  # vpc
  # ##############################
  vpc_cidr     = "10.0.0.0/16"
  subnet_count = 2

  # ##############################
  # eks
  # ##############################
  kubernetes_version = "1.32"
  node_instance_type = "t3.medium" # Budget 
  node_count         = 2

  # ##############################
  # workload under observation
  # ##############################
  app_namespace = "incident-demo"
  app_name      = "aiops-agentcore-workload"

  # ##############################
  # lambda
  # ##############################
  lambda_trigger_image_tag = "latest"

  # ##############################
  # bedrock knowledge base
  # ##############################
  bedrock_embedding_model = "amazon.titan-embed-text-v2:0"
  bedrock_embedding_dims  = 1024
  runbook_s3_prefix       = "runbook/"

  # ##############################
  # agent
  # ##############################
  # The global. inference-profile prefix is required; the bare model id fails.
  agent_model_id  = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
  agent_image_tag = "latest"

}
