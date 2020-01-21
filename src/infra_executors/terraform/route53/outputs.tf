output "primary_zone_id" {
  value = aws_route53_zone.primary.id
}

output "subdomains" {
  value = aws_route53_record.subdomains.*.name
}
