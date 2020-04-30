output "bucket" {
  value = aws_s3_bucket.statics.id
}

output "arn" {
  value = aws_s3_bucket.statics.arn
}

output "bucket_domain_name" {
  value = aws_s3_bucket.statics.bucket_domain_name
}

output "bucket_regional_domain_name" {
  value = aws_s3_bucket.statics.bucket_regional_domain_name
}

output "r53_zone_id" {
  value = aws_s3_bucket.statics.hosted_zone_id
}

output "region" {
  value = aws_s3_bucket.statics.region
}

output "website_endpoint" {
  value = aws_s3_bucket.statics.website_endpoint
}

output "website_domain" {
  value = aws_s3_bucket.statics.website_domain
}
