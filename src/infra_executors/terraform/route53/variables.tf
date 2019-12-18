variable "domain" {
  type = string
  description = "Domain name. Example: example.com"
}

variable "enviroment" {
  type = string
  default = "development"
  description = "Name of the environment. All resources will be tagged with this."
}

variable "cname_subdomains" {
  type = string
  default = ""
  description = "Comma separated list of CNAME subdomains. Example: 'test,dev,staging'"
}
