# # bedrock-s3.tf

# # #################################
# # Runbook source
# # #################################
# data "aws_s3_bucket" "kube_agent" {
#   bucket = "${local.project_name}-project-${data.aws_caller_identity.current.account_id}"
# }

# # Uploaded from the repo
# resource "aws_s3_object" "runbook" {
#   bucket = data.aws_s3_bucket.kube_agent.id
#   key    = "${local.runbook_s3_prefix}oom-troubleshooting.md"
#   source = "${path.module}/../../runbook/oom-troubleshooting.md"
#   etag   = filemd5("${path.module}/../../runbook/oom-troubleshooting.md")
# }
