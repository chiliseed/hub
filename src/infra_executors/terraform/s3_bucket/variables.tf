variable "bucket_name" {
  type = string
}

variable "acl" {
  type = string
  default = "private"
}

variable "enviroment" {
  type = string
  default = "development"
  description = "Name of the environment. All resources will be tagged with this."
}
