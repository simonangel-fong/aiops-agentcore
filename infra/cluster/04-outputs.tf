# output.tf

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${local.aws_region} --name ${module.eks.cluster_name}"
}
output "agent_runtime_arn" {
  value = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn
}
