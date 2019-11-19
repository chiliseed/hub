# ---------------------------------------------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
# Define these secrets as environment variables
# ---------------------------------------------------------------------------------------------------------------------

# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY
# AWS_DEFAULT_REGION
# AWS_SESSION_TOKEN - if the role has mfa enabled

variable "environment" {
  default     = "development"
  description = "The name of the environment being built. This will be used to tag all resources."
}

variable "vpc_cidr" {
  description = "VPC cidr block to use. Example: 10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  type = "list"
}

variable "public_subnet_cidrs" {
  type = "list"
}

variable "availability_zones" {
  type = "list"
}
//
//variable "db_identifier" {
//  description = "A unique identifier of the db. One Postgres can have multiple databases. This is the identifier of the Postgres."
//}
//
//variable "db_name" {
//  description = "DB name"
//}
//
//variable "db_username" {
//  description = "DB username"
//}
//
//variable "db_password" {
//  description = "DB password"
//}
//
//variable "db_instance_type" {
//  default     = "db.t2.large"
//  description = "The type of the instance to use for the db. Example: db.t2.large"
//}
//variable "db_allocated_storage" {
//  default     = 5
//  description = "The allocated storage in gigabytes."
//}

//variable "domain" {
//  description = "Domain name. Example: example.com"
//  type        = string
//}
