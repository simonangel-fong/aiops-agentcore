# variables.tf

# ##############################
# notification
# ##############################
variable "sns_incident_email" {
  description = "Address subscribed to the incident report topic"
  type        = string
}

# ##############################
# slack
# ##############################
variable "slack_team_id" {
  description = "Slack workspace id (T...)"
  type        = string
  default     = ""
}

variable "slack_channel_id" {
  description = "Slack channel id (C...)"
  type        = string
  default     = ""
}
