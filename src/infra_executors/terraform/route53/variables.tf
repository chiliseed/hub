variable "domain" {
  type = string
  description = "Domain name. Example: example.com"
}

variable "env_name" {
  type = string
  description = "Name of the environment. All resources will be tagged with this."
}

variable "cname_subdomains" {
  type = list(object({
    subdomain = string
    route_to = string
  }))
  default = []
  description = "Comma separated list of CNAME subdomains and where to route traffic to. route_to can be load balancer dns name or cloudfront dns."
}
