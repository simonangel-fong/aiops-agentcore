# output.tf

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${local.aws_region} --name ${module.eks.cluster_name}"
}