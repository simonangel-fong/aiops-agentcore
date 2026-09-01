# cloudflare.tf

# #################################
# Cloudflare DNS
# #################################
resource "cloudflare_record" "site" {
  zone_id = var.cloudflare_zone_id
  name    = split(".", local.site_domain)[0]
  type    = "CNAME"
  content = aws_cloudfront_distribution.site.domain_name
  proxied = false
  ttl     = 300
  comment = "${local.project_name} project dns."
}
