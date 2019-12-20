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
