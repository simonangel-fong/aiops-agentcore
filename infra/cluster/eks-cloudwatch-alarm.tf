# eks-cloudwatch-alarm.tf

# #################################
# Container restart alarm
# #################################
resource "aws_cloudwatch_metric_alarm" "container_restart" {
  alarm_name        = "${local.prefix_name}-container-restart"
  alarm_description = "Container restarted in ${local.app_namespace}/${local.app_name}."

  namespace   = "ContainerInsights"
  metric_name = "pod_number_of_container_restarts"
  statistic   = "Maximum"

  dimensions = {
    ClusterName = local.project_name
    Namespace   = local.app_namespace
    PodName     = local.app_name
  }

  # > 1 per 60s
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 1
  period              = 60
  evaluation_periods  = 1

  # if missing data
  treat_missing_data = "notBreaching"
}
