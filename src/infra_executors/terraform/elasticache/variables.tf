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
  default     = "cache.t2.small"
  description = "The type of the instance to use for the cache. Example: cache.t2.small"
}

variable "identifier" {
  type        = string
  description = "A unique identifier of the cache."
}

variable "engine" {
  type        = string
  default     = "redis"
  description = "One of: redis or memcached"
}

variable "number_of_nodes" {
  type        = number
  default     = 1
  description = "Number of nodes to launch in a cluster. Defaults to primary server only."
}

variable "parameter_group_name" {
  type    = string
  default = "default.redis5.0"
}

variable "engine_version" {
  type        = string
  default     = "5.0.6"
  description = "Engine version to run the cache server."
}

variable "allowed_security_groups_ids" {
  description = "Security groups which will be allowed to connect to the DB."
  type        = list(string)
  default     = []
}

variable "apply_immediately" {
  type        = bool
  default     = true
  description = "Whethere changes should be applied immediately or at the next maintenance window."
}

variable "snapshot_retention_limit_days" {
  type        = number
  default     = 0 # backup turned off
  description = "The number of days for which ElastiCache will retain automatic cache cluster snapshots before deleting them. not supported on cache.t1.micro or cache.t2.* cache nodes."
}
