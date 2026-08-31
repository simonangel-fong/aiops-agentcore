# vpc.tf

data "aws_availability_zones" "available" {
  state = "available"
}

# #################################
# VPC
# #################################
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = local.prefix_name
  cidr = local.vpc_cidr

  azs            = slice(data.aws_availability_zones.available.names, 0, local.subnet_count)
  public_subnets = [for i in range(local.subnet_count) : cidrsubnet(local.vpc_cidr, 8, i)]

  enable_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  # enable NAT
  map_public_ip_on_launch = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1" # load balancer placement.
  }
}

