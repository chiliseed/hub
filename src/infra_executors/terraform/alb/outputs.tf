// target group arns for ecs launch configuration for registration with the alb
output "target_groups_arn" {
  value = aws_alb_target_group.this.*.arn
}

// for ecs security group to have a rule for only inbound traffic from alb
output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

// for route53 cname subdomain
output "public_dns" {
  value = aws_alb.alb.dns_name
}

output "alb_arn" {
  value = aws_alb.alb.arn
}

output "alb_name" {
  value = aws_alb.alb.name
}
