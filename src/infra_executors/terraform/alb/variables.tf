variable "env_name" {
  type        = string
  description = "The name of the environment"
}

variable "alb_name" {
  type        = string
  description = "The name of the ALB instance."
}

variable "vpc_id" {
  type = string
}

variable "internal" {
  type        = bool
  default     = false
  description = "If true, internal facing alb will be created. Otherwise, public facing alb will be created"
}

variable "idle_timeout" {
  type        = string
  default     = "60"
  description = "The time in seconds that the connection is allowed to be idle."
}

variable "deregistration_delay" {
  default     = "300"
  description = "The default deregistration delay"
}

//variable "ssl_certificate_arn" {
//  type = string
//  default = ""
//  description = "ARN of a related ACM certificate to use for https."
//}

// open ports internally talk to containers on ecs over http.
// externally, ports are setup with https listeners and http redirect to https.
// container_port -> used in target group and tells on what port alb is contacting the servers
// alb_port -> used in alb listener, tells on what port alb is listening to incoming web traffic
variable "open_ports" {
  type = list(object({
    name = string
    container_port = number
    alb_port_https = number
    alb_port_http = number
    health_check_endpoint = string
    health_check_protocol = string
    ssl_certificate_arn = string
  }))
}
