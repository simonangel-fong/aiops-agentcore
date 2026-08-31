# bedrock.tf

# #################################
# IAM: Bedrock knowledge base
# #################################
data "aws_region" "current" {}

resource "aws_iam_role" "kb" {
  name = "${local.prefix_name}-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

resource "aws_iam_role_policy" "kb" {
  name = "${local.prefix_name}-kb-policy"
  role = aws_iam_role.kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = "arn:aws:bedrock:${data.aws_region.current.region}::foundation-model/${local.bedrock_embedding_model}"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [data.aws_s3_bucket.kube_agent.arn, "${data.aws_s3_bucket.kube_agent.arn}/*"]
      },
      {
        Effect = "Allow"
        Action = [
          "s3vectors:GetIndex",
          "s3vectors:QueryVectors",
          "s3vectors:PutVectors",
          "s3vectors:GetVectors",
          "s3vectors:DeleteVectors",
          "s3vectors:ListVectors",
        ]
        Resource = aws_s3vectors_index.kb.index_arn
      },
    ]
  })
}

# #################################
# Bedrock: Vector store
# #################################
# S3 Vectors
resource "aws_s3vectors_vector_bucket" "kb" {
  vector_bucket_name = "${local.prefix_name}-vectors"
}

resource "aws_s3vectors_index" "kb" {
  vector_bucket_name = aws_s3vectors_vector_bucket.kb.vector_bucket_name
  index_name         = "${local.prefix_name}-runbook"

  data_type       = "float32"
  dimension       = local.bedrock_embedding_dims # Specifies the length of vector array 
  distance_metric = "cosine"

  metadata_configuration {
    non_filterable_metadata_keys = [
      "AMAZON_BEDROCK_TEXT",
      "AMAZON_BEDROCK_METADATA",
    ]
  }
}

# #################################
# Bedrock: Knowledge base
# #################################
resource "aws_bedrockagent_knowledge_base" "runbook" {
  name        = "${local.prefix_name}-runbook"
  description = "Troubleshooting runbook for the incident triage agent"
  role_arn    = aws_iam_role.kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.region}::foundation-model/${local.bedrock_embedding_model}"
    }
  }

  storage_configuration {
    type = "S3_VECTORS"
    s3_vectors_configuration {
      index_arn = aws_s3vectors_index.kb.index_arn
    }
  }

  depends_on = [aws_iam_role_policy.kb]
}

resource "aws_bedrockagent_data_source" "runbook" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.runbook.id
  name              = "${local.prefix_name}-runbook-s3"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn         = data.aws_s3_bucket.kube_agent.arn
      inclusion_prefixes = [local.runbook_s3_prefix]
    }
  }
}
