output "security_group_id" {
  value = module.ecs_instances.ecs_instance_security_group_id
}

output "cluster" {
  value = aws_ecs_cluster.cluster.name
}

output "ecs_executor_role_arn" {
  value = module.ecs_task_executor_role.role_arn
}
