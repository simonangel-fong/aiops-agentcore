# output.tf

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${local.aws_region} --name ${module.eks.cluster_name}"
}

output "agent_runtime_arn" {
  value = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn
}

output "bedrock_kb_id" {
  value = aws_bedrockagent_knowledge_base.runbook.id
}

output "bedrock_kb_data_source_id" {
  value = aws_bedrockagent_data_source.runbook.data_source_id
}
