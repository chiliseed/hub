locals {
  bucket_name = "${var.environment}.${var.domain}"
  logs_bucket = "access-logs.${local.bucket_name}"
}


resource "aws_cloudfront_origin_access_identity" "origin_access_identity" {
  comment = "Cloudfront access identify for s3 bucket on ${var.environment}, serving website ${local.bucket_name}"
}

data "aws_iam_policy_document" "ui-policy" {
  statement {
    sid       = "1"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${local.bucket_name}/*"]
    effect    = "Allow"

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.origin_access_identity.iam_arn]
    }
  }

  statement {
    sid       = "2"
    actions   = ["s3:ListBucket"]
    effect    = "Allow"
    resources = ["arn:aws:s3:::${local.bucket_name}"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.origin_access_identity.iam_arn]
    }

  }
}

resource "aws_s3_bucket" "ui" {
  bucket = local.bucket_name
  policy = data.aws_iam_policy_document.ui-policy.json

  website {
    index_document = "index.html"
  }

  tags = {
    Name        = local.bucket_name
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "cloudfront-logs" {
  bucket = local.logs_bucket
  acl    = "log-delivery-write"

  tags = {
    Name        = local.logs_bucket
    Environment = var.environment
  }
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name = aws_s3_bucket.ui.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.ui.bucket

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.origin_access_identity.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Cloufront distribution for ${local.bucket_name}"
  default_root_object = "index.html"

  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.cloudfront-logs.bucket_domain_name
  }

  aliases = [local.bucket_name]

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_s3_bucket.ui.bucket

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
//    iam_certificate_id       = var.ssl_certificate_id
    acm_certificate_arn      = var.ssl_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1"
  }

  custom_error_response {
    error_code    = 403
    response_code = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code    = 404
    response_code = 200
    response_page_path = "/index.html"
  }

  tags = {
    Environment = var.environment
    Name        = local.bucket_name
  }
}

resource "aws_route53_record" "domain" {
  zone_id = var.route_53_zone_id
  name = local.bucket_name
  type    = "A"
  alias {
    name = aws_cloudfront_distribution.s3_distribution.domain_name
    zone_id = "Z2FDTNDATAQYW2" # CloudFront ZoneID
    evaluate_target_health = false
  }
}
