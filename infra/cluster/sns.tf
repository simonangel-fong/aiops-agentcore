# sns.tf


# #################################
# IAM: SNS
# #################################
# allow trigger lambda to publish topic
resource "aws_sns_topic_policy" "incident" {
  arn = aws_sns_topic.incident.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = aws_iam_role.trigger.arn }
      Action    = "sns:Publish"
      Resource  = aws_sns_topic.incident.arn
    }]
  })
}

# allow publish
resource "aws_iam_role_policy" "trigger_publish" {
  name = "${local.prefix_name}-trigger-publish"
  role = aws_iam_role.trigger.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sns:Publish"
      Resource = aws_sns_topic.incident.arn
    }]
  })
}

# #################################
# SNS: Incident report topic
# #################################
resource "aws_sns_topic" "incident" {
  name = "${local.prefix_name}-incident"
}

# sub: email
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.incident.arn
  protocol  = "email"
  endpoint  = var.sns_incident_email
}
