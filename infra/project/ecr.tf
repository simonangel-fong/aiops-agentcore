# ecr.tf

# #################################
# ECR
# #################################
resource "aws_ecr_repository" "this" {
  for_each = toset(local.ecr_repo_list)

  name                 = "${local.project_name}-${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep only last 5
resource "aws_ecr_lifecycle_policy" "this" {
  for_each = aws_ecr_repository.this

  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# #################################
# State moves: per-repo resources -> for_each
# Safe to delete once applied in every workspace.
# #################################
moved {
  from = aws_ecr_repository.app
  to   = aws_ecr_repository.this["app"]
}

moved {
  from = aws_ecr_repository.trigger
  to   = aws_ecr_repository.this["trigger"]
}

moved {
  from = aws_ecr_repository.agent
  to   = aws_ecr_repository.this["agent"]
}

moved {
  from = aws_ecr_lifecycle_policy.app
  to   = aws_ecr_lifecycle_policy.this["app"]
}

moved {
  from = aws_ecr_lifecycle_policy.trigger
  to   = aws_ecr_lifecycle_policy.this["trigger"]
}

moved {
  from = aws_ecr_lifecycle_policy.agent
  to   = aws_ecr_lifecycle_policy.this["agent"]
}
