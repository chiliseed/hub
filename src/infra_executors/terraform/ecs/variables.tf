variable "env_name" {
  description = "The name of the environment"
}

variable "cluster" {
  description = "The name of the ECS cluster"
}

variable "instance_group" {
  default     = "default"
  description = "The name of the instances that you consider as a group"
}

variable "max_size" {
  description = "Maximum size of the nodes in the cluster"
  default     = 1
}

variable "min_size" {
  description = "Minimum size of the nodes in the cluster"
  default     = 1
}

variable "desired_capacity" {
  description = "The desired capacity of the cluster"
  default     = 1
}

variable "ssh_key_name" {
  description = "SSH key name to be used"
}

variable "instance_type" {
  description = "AWS instance type to use"
  default     = "t2.micro"
}

variable "ecs_aws_ami" {
  description = "The AWS ami id to use for ECS according to aws region"
}

variable "custom_userdata" {
  default     = ""
  description = "Inject extra command in the instance template to be run on boot"
}

variable "ecs_config" {
  default     = "echo '' > /etc/ecs/ecs.config"
  description = "Specify ecs configuration or get it from S3. Example: aws s3 cp s3://some-bucket/ecs.config /etc/ecs/ecs.config"
}

variable "cloudwatch_prefix" {
  default     = ""
  description = "If you want to avoid cloudwatch collision or you don't want to merge all logs to one log group specify a prefix"
}

variable "vpc_id" {
  type = string
}

variable "alb_security_group_id" {
  type = string
  default = ""
}

variable "project_name" {
  description = "Project name for which this alb is created"
}
