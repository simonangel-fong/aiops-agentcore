# agentcore.tf

# ECR: agent
data "aws_ecr_image" "agent" {
  repository_name = "${local.project_name}-agent"
  image_tag       = local.agent_image_tag
}

# #################################
# IAM: agentcore
# #################################
resource "aws_iam_role" "agent" {
  name = "${local.prefix_name}-role-agent"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock-agentcore.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

resource "aws_iam_role_policy" "agent" {
  name = "${local.prefix_name}-agent-policy"
  role = aws_iam_role.agent.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:${local.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:Retrieve"]
        Resource = aws_bedrockagent_knowledge_base.runbook.arn
      },
      {
        # Read-only metrics. GetMetricData/Statistics take no resource ARN.
        Effect   = "Allow"
        Action   = ["cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["eks:DescribeCluster"]
        Resource = module.eks.cluster_arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
        ]
        Resource = "arn:aws:logs:${local.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]
        Resource = "arn:aws:ecr:${local.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${local.project_name}-agent"
      },
    ]
  })
}


# #################################
# AgentCore: Runtime
# #################################
resource "aws_bedrockagentcore_agent_runtime" "agent" {
  agent_runtime_name = replace("${local.prefix_name}-agent", "-", "_")
  role_arn           = aws_iam_role.agent.arn
  description        = "Kubernetes OOM incident triage agent"

  agent_runtime_artifact {
    container_configuration {
      container_uri = data.aws_ecr_image.agent.image_uri
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  protocol_configuration {
    server_protocol = "HTTP"
  }

  environment_variables = {
    KNOWLEDGE_BASE_ID = aws_bedrockagent_knowledge_base.runbook.id
    CLUSTER_NAME      = module.eks.cluster_name
    AGENT_MODEL_ID    = local.agent_model_id
  }

  depends_on = [aws_iam_role_policy.agent]
}
