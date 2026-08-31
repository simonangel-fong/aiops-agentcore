# lambda.tf

# ECR
data "aws_ecr_image" "trigger" {
  repository_name = "${local.project_name}-trigger"
  image_tag       = local.lambda_trigger_image_tag
}

# #################################
# IAM: lambda
# #################################
resource "aws_iam_role" "trigger" {
  name = "${local.prefix_name}-role-lambda-trigger"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "trigger_logs" {
  role       = aws_iam_role.trigger.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# allow invoke agent
resource "aws_iam_role_policy" "trigger_invoke_agent" {
  name = "${local.prefix_name}-trigger-invoke-agent"
  role = aws_iam_role.trigger.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "bedrock-agentcore:InvokeAgentRuntime"
      Resource = [
        aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn,
        "${aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn}/*",
      ]
    }]
  })
}

# #################################
# Lambda: log group
# #################################
resource "aws_cloudwatch_log_group" "trigger" {
  name              = "/aws/lambda/${local.prefix_name}-trigger"
  retention_in_days = 7
}

# #################################
# Lambda Function
# #################################
resource "aws_lambda_function" "trigger" {
  function_name = "${local.prefix_name}-trigger"
  role          = aws_iam_role.trigger.arn

  package_type = "Image"
  image_uri    = data.aws_ecr_image.trigger.image_uri

  # 5 min
  timeout = 300

  environment {
    variables = {
      AGENT_RUNTIME_ARN = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn # agent runtime arn
      SNS_TOPIC_ARN     = aws_sns_topic.incident.arn                                 # sns
    }
  }

  depends_on = [aws_cloudwatch_log_group.trigger]
}
