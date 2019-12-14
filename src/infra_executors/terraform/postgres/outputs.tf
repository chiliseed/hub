// Master details
output "master_instance_address" {
  description = "The address of the RDS instance"
  value       = module.master.instance_address
}

output "master_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = module.master.instance_arn
}

output "master_instance_availability_zone" {
  description = "The availability zone of the RDS instance"
  value       = module.master.instance_availability_zone
}

output "master_instance_endpoint" {
  description = "The connection endpoint"
  value       = module.master.instance_endpoint
}

output "master_instance_hosted_zone_id" {
  description = "The canonical hosted zone ID of the DB instance (to be used in a Route 53 Alias record)"
  value       = module.master.instance_hosted_zone_id
}

output "master_instance_id" {
  description = "The RDS instance ID"
  value       = module.master.instance_id
}

output "master_instance_resource_id" {
  description = "The RDS Resource ID of this instance"
  value       = module.master.instance_resource_id
}

output "master_instance_status" {
  description = "The RDS instance status"
  value       = module.master.instance_status
}

output "master_instance_name" {
  description = "The database name"
  value       = module.master.instance_name
}

output "master_instance_username" {
  description = "The master username for the database"
  value       = module.master.instance_username
}

output "master_instance_password" {
  description = "The database password (this password may be old, because Terraform doesn't track it after initial creation)"
  value       = var.password
}

output "master_instance_port" {
  description = "The database port"
  value       = module.master.instance_port
}

output "master_subnet_group_id" {
  description = "The db subnet group name"
  value       = module.master.subnet_group_id
}

output "master_subnet_group_arn" {
  description = "The ARN of the db subnet group"
  value       = module.master.subnet_group_arn
}

output "master_parameter_group_id" {
  description = "The db parameter group id"
  value       = module.master.parameter_group_id
}

output "master_parameter_group_arn" {
  description = "The ARN of the db parameter group"
  value       = module.master.parameter_group_arn
}

output "master_option_group_id" {
  description = "The db option group id"
  value       = module.master.option_group_id
}

output "master_option_group_arn" {
  description = "The ARN of the db option group"
  value       = module.master.option_group_arn
}


// Readreplica details
output "read_instance_address" {
  description = "The address of the RDS instance"
  value       = module.read-replica.instance_address
}

output "read_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = module.read-replica.instance_arn
}

output "read_instance_availability_zone" {
  description = "The availability zone of the RDS instance"
  value       = module.read-replica.instance_availability_zone
}

output "read_instance_endpoint" {
  description = "The connection endpoint"
  value       = module.read-replica.instance_endpoint
}

output "read_instance_hosted_zone_id" {
  description = "The canonical hosted zone ID of the DB instance (to be used in a Route 53 Alias record)"
  value       = module.read-replica.instance_hosted_zone_id
}

output "read_instance_id" {
  description = "The RDS instance ID"
  value       = module.read-replica.instance_id
}

output "read_instance_resource_id" {
  description = "The RDS Resource ID of this instance"
  value       = module.read-replica.instance_resource_id
}

output "read_instance_status" {
  description = "The RDS instance status"
  value       = module.read-replica.instance_status
}

output "read_instance_name" {
  description = "The database name"
  value       = module.read-replica.instance_name
}

output "read_instance_username" {
  description = "The read username for the database"
  value       = module.read-replica.instance_username
}

output "read_instance_password" {
  description = "The database password (this password may be old, because Terraform doesn't track it after initial creation)"
  value       = var.password
}

output "read_instance_port" {
  description = "The database port"
  value       = module.read-replica.instance_port
}

output "read_subnet_group_id" {
  description = "The db subnet group name"
  value       = module.read-replica.subnet_group_id
}

output "read_subnet_group_arn" {
  description = "The ARN of the db subnet group"
  value       = module.read-replica.subnet_group_arn
}

output "read_parameter_group_id" {
  description = "The db parameter group id"
  value       = module.read-replica.parameter_group_id
}

output "read_parameter_group_arn" {
  description = "The ARN of the db parameter group"
  value       = module.read-replica.parameter_group_arn
}

output "read_option_group_id" {
  description = "The db option group id"
  value       = module.read-replica.option_group_id
}

output "read_option_group_arn" {
  description = "The ARN of the db option group"
  value       = module.read-replica.option_group_arn
}

output "security_group_id" {
  description = "DB security group"
  value       = aws_security_group.db.id
}
