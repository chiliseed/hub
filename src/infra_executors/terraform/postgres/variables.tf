variable "environment" {
  default     = "development"
  description = "The name of the environment being built. This will be used to tag all resources."
  type        = string
}

variable "vpc_id" {
  type        = string
  description = "The id of the vpc into which to install the db."
}

variable "instance_type" {
  type        = string
  default     = "db.t2.large"
  description = "The type of the instance to use for the db. Example: db.t2.large"
}

variable "allocated_storage" {
  type        = number
  default     = 5
  description = "The allocated storage in gigabytes."
}

variable "identifier" {
  type        = string
  description = "A unique identifier of the db. One Postgres can have multiple databases. This is the identifier of the Postgres."
}

variable "name" {
  description = "Database name"
  type        = string
}

variable "username" {
  description = "DB username"
  type        = string
}

variable "password" {
  description = "DB password"
  type        = string
}
