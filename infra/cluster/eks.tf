# eks.tf

# #################################
# EKS
# #################################
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = local.project_name
  kubernetes_version = local.kubernetes_version

  # #################################
  # network
  # #################################
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  # #################################
  # security
  # #################################
  enabled_log_types                        = ["api", "audit"]
  endpoint_public_access                   = true
  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true

  # #################################
  # addons
  # #################################
  addons = {
    vpc-cni = {
      before_compute = true
      most_recent    = true
    }
    kube-proxy = {
      before_compute = true
      most_recent    = true
    }
    coredns = {
      most_recent = true
    }
    amazon-cloudwatch-observability = {}
  }

  # #################################
  # node group
  # #################################
  eks_managed_node_groups = {
    bootstrap = {
      instance_types = [local.node_instance_type]

      desired_size = local.node_count
      min_size     = 0
      max_size     = local.node_count

      subnet_ids = module.vpc.public_subnets

      iam_role_additional_policies = {
        cloudwatch = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
      }
    }
  }
}
