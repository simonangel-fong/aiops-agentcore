# cloudfront.tf

# #################################
# ACM certificate (us-east-1)
# #################################
data "aws_acm_certificate" "site" {
  provider = aws.us_east_1

  domain      = local.site_cert_domain
  statuses    = ["ISSUED"]
  most_recent = true
}

# Only this distribution may read the bucket.
resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.aiops_argentcore.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontRead"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      # Scoped to the site prefix: the rest of this bucket holds Terraform
      # state and must stay unreadable from the distribution.
      Resource = "${aws_s3_bucket.aiops_argentcore.arn}/${local.site_prefix}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.site.arn
        }
      }
    }]
  })
}

# #################################
# Site content
# #################################
resource "aws_s3_object" "site" {
  for_each = fileset(local.site_root, "**")

  bucket = aws_s3_bucket.aiops_argentcore.id
  key    = "${local.site_prefix}/${each.value}"
  source = "${local.site_root}/${each.value}"
  etag   = filemd5("${local.site_root}/${each.value}")

  content_type = lookup(
    local.site_mime_types,
    lower(reverse(split(".", each.value))[0]),
    "application/octet-stream"
  )

  cache_control = endswith(each.value, ".html") ? "public, max-age=0, must-revalidate" : "public, max-age=86400"
}

# #################################
# CloudFront
# #################################
resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${local.prefix_name}-site"
  description                       = "OAC for ${local.site_domain}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "site" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = local.site_domain
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  aliases             = [local.site_domain]

  origin {
    domain_name              = aws_s3_bucket.aiops_argentcore.bucket_regional_domain_name
    origin_id                = local.site_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id

    # Serve the site out of the web/ prefix, so "/" maps to web/index.html.
    origin_path = "/${local.site_prefix}"
  }

  default_cache_behavior {
    target_origin_id       = local.site_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # Managed-CachingOptimized
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  custom_error_response {
    error_code            = 403
    response_code         = 404
    response_page_path    = "/error.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 404
    response_page_path    = "/error.html"
    error_caching_min_ttl = 10
  }

  viewer_certificate {
    acm_certificate_arn      = data.aws_acm_certificate.site.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}
