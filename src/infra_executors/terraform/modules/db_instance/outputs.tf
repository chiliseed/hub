output "this_db_instance_address" {
  description = "The address of the RDS instance"
  value       = concat(aws_db_instance.db.*.address, [""])[0]
}

output "this_db_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = concat(aws_db_instance.db.*.arn, [""])[0]
}

output "this_db_instance_availability_zone" {
  description = "The availability zone of the RDS instance"
  value       = concat(aws_db_instance.db.*.availability_zone, [""])[0]
}

output "this_db_instance_endpoint" {
  description = "The connection endpoint"
  value       = concat(aws_db_instance.db.*.endpoint, [""])[0]
}

output "this_db_instance_hosted_zone_id" {
  description = "The canonical hosted zone ID of the DB instance (to be used in a Route 53 Alias record)"
  value       = concat(aws_db_instance.db.*.hosted_zone_id, [""])[0]
}

output "this_db_instance_id" {
  description = "The RDS instance ID"
  value       = concat(aws_db_instance.db.*.id, [""])[0]
}

output "this_db_instance_resource_id" {
  description = "The RDS Resource ID of this instance"
  value       = concat(aws_db_instance.db.*.resource_id, [""])[0]
}

output "this_db_instance_status" {
  description = "The RDS instance status"
  value       = concat(aws_db_instance.db.*.status, [""])[0]
}

output "this_db_instance_name" {
  description = "The database name"
  value       = concat(aws_db_instance.db.*.name, [""])[0]
}

output "this_db_instance_username" {
  description = "The master username for the database"
  value       = concat(aws_db_instance.db.*.username, [""])[0]
}

output "this_db_instance_port" {
  description = "The database port"
  value       = concat(aws_db_instance.db.*.port, [""])[0]
}
