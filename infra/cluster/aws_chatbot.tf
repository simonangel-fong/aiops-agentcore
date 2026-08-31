# # slack.tf

# locals {
#   slack_enabled = var.slack_team_id != "" && var.slack_channel_id != ""
# }

# # #################################
# # IAM: slack
# # #################################
# resource "aws_iam_role" "slack" {
#   count = local.slack_enabled ? 1 : 0

#   name = "${local.prefix_name}-slack-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect    = "Allow"
#       Principal = { Service = "chatbot.amazonaws.com" }
#       Action    = "sts:AssumeRole"
#     }]
#   })
# }

# # Read-only: the channel renders notifications
# resource "aws_iam_role_policy_attachment" "slack" {
#   count = local.slack_enabled ? 1 : 0

#   role       = aws_iam_role.slack[0].name
#   policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
# }

# # #################################
# # AWS chatbot
# # #################################
# resource "aws_chatbot_slack_channel_configuration" "incident" {
#   count = local.slack_enabled ? 1 : 0

#   configuration_name = "${local.prefix_name}-incident"
#   iam_role_arn       = aws_iam_role.slack[0].arn
#   slack_team_id      = var.slack_team_id    # slack workspace
#   slack_channel_id   = var.slack_channel_id # slack channel

#   sns_topic_arns = [aws_sns_topic.incident.arn]

#   # Notifications only; no command execution from the channel.
#   user_authorization_required = true
# }
