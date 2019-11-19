variable "environment" {
  description = "The name of the environment"
}

variable "cluster" {
  default     = "default"
  description = "The name of the ECS cluster"
}

variable "instance_group" {
  default     = "default"
  description = "The name of the instances that you consider as a group"
}

variable "load_balancers" {
  type        = "list"
  default     = []
  description = "The load balancers to couple to the instances"
}

variable "max_size" {
  description = "Maximum size of the nodes in the cluster"
}

variable "min_size" {
  description = "Minimum size of the nodes in the cluster"
}

variable "desired_capacity" {
  description = "The desired capacity of the cluster"
}

variable "key_name" {
  description = "SSH key name to be used"
}

variable "instance_type" {
  description = "AWS instance type to use"
}

variable "ecs_aws_ami" {
  description = "The AWS ami id to use for ECS"
}

variable "custom_userdata" {
  default     = ""
  description = "Inject extra command in the instance template to be run on boot"
}

variable "ecs_config" {
  default     = "echo '' > /etc/ecs/ecs.config"
  description = "Specify ecs configuration or get it from S3. Example: aws s3 cp s3://some-bucket/ecs.config /etc/ecs/ecs.config"
}

variable "ecs_logging" {
  default     = "[\"json-file\",\"awslogs\"]"
  description = "Adding logging option to ECS that the Docker containers can use. It is possible to add fluentd as well"
}

variable "cloudwatch_prefix" {
  default     = ""
  description = "If you want to avoid cloudwatch collision or you don't want to merge all logs to one log group specify a prefix"
}

variable "subdomain" {
  description = "Subdomain. Example: dev.example.com"
  type        = string
}

variable "domain" {
  description = "Domain name. Example: example.com"
  type        = string
}

variable "health_check_path" {
  description = "The health check endoint for dashboard backend."
  type        = string
}

variable "route_53_zone_id" {
  description = "The id of the route 53 zone under which subdomain will be created."
  type        = string
}

variable "ssl_certificate_arn" {
  description = "The SSL certificate arn."
  type        = string
}

variable "load_balancer_idle_timeout" {
  type        = string
  default     = "60"
  description = "The time in seconds that the connection is allowed to be idle."
}

variable "public_subnet_ids" {
  type = "list"
  description = "List of public subnet group ids."
}

variable "vpc_id" {
  type = "string"
}

variable "db_security_group_id" {
  type = "string"
  description = "The id of the security group assigned to the db."
}

variable "ecs_iam_instance_role_id" {
  type = "string"
  description = "The id of the IAM role that will be assigned to ECS servers."
}
