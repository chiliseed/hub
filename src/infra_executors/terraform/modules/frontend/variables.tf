variable "environment" {
  description = "The name of the environment in configuration. Example: staging"
  type        = string
}

variable "domain" {
  description = "Domain name. Example: example.com"
  type        = string
}

variable "route_53_zone_id" {
  description = "The id of the route 53 zone under which subdomain will be created."
  type        = string
}

variable "ssl_certificate_arn" {
  description = "The SSL certificate arn."
  type        = string
}

//variable "ssl_certificate_id" {
//  description = "The SSL certificate ID."
//  type        = string
//}
