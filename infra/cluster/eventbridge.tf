# eventbridge.tf

# #################################
# IAM: Eventbridge with lambda
# #################################
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.container_restart.arn
}

# #################################
# Eventbridge: Cloudwatch event rule
# #################################
resource "aws_cloudwatch_event_rule" "container_restart" {
  name        = "${local.prefix_name}-container-restart"
  description = "Container restart alarm entering ALARM state"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      alarmName = [aws_cloudwatch_metric_alarm.container_restart.alarm_name]
      state = {
        value = ["ALARM"]
      }
    }
  })
}

# #################################
# Eventbridge: Cloudwatch event target
# #################################
resource "aws_cloudwatch_event_target" "trigger" {
  rule      = aws_cloudwatch_event_rule.container_restart.name
  target_id = "trigger-lambda"
  arn       = aws_lambda_function.trigger.arn
}
