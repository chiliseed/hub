variable "worker_ami" {
  type    = string
  default = "ami-05a0fe32efb5fecea"
}

variable "ssh_key_name" {
  type = string
}

variable "spot_max_price" {
  type    = string
  default = "0.03"
}

variable "aws_access_key_id" {
  type = string
}

variable "aws_access_key_secret" {
  type = string
}

variable "env_name" {
  type = string
}

variable "code_version" {
  type = string
}

variable "dockerfile_target" {
  type    = string
  default = ""
  description = "Specific dockerfile stage to build."
}

variable "dockerfile" {
  type    = string
  default = ""
  description = "Path from project root to desired dockerfile for the service."
}

variable "service_name" {
  type = string
}

variable "ecr_url" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "valid_until" {
  type        = string
  description = "The end date and time of the request, in UTC RFC3339 format(for example, YYYY-MM-DDTHH:MM:SSZ)"
}

variable "build_tool_version" {
  type = string
  description = "Version of chiliseed build worker tool to be pulled from S3"
  default = "0.1.0"
}
