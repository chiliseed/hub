output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "default_alb_target_group" {
  value = aws_alb_target_group.dashboard_api.arn
}

output "public_dns" {
  value = aws_alb.alb.dns_name
}

output "target_group_arns" {
  value = list(
          aws_alb_target_group.dashboard_api_external.arn,
          aws_alb_target_group.dashboard_api.arn,
          aws_alb_target_group.mission_manager.arn,
          aws_alb_target_group.test_frontend.arn
  )
}
