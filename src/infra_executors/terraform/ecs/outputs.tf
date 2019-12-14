output "security_group_id" {
  value = module.ecs_instances.ecs_instance_security_group_id
}

output "cluster" {
  value = aws_ecs_cluster.cluster.name
}
