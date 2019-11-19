output "default_alb_target_group" {
  value = module.alb.default_alb_target_group
}

output "task_executor_role_arn" {
  value = module.ecs_task_executor_role.role_arn
}
