# eks-access-agentcore.tf

# #################################
# EKS: Kubernetes access
# #################################
resource "aws_eks_access_entry" "agent" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.agent.arn
  type          = "STANDARD"
}

# RBAC read-only
resource "aws_eks_access_policy_association" "agent" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.agent.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"

  access_scope {
    type       = "namespace"
    namespaces = [local.app_namespace]
  }

  depends_on = [aws_eks_access_entry.agent]
}
