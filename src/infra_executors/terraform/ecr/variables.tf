variable "env_name" {
  type        = string
  description = "The name of the environment"
}

variable "repositories" {
  type = list(string)
  description = "A list of repository names to create"
}
