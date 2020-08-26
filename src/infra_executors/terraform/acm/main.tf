terraform {
  required_version = ">=0.12.29"
  backend "s3" {
    bucket = "chiliseed-dev-terraform-states"
    region = "us-east-2"
    //    key    = "path/to.tfstate"  this will be provided on runtime
  }
  required_providers {
    aws      = "~> 2.70.0"
    null     = "~> 2.1.2"
    random   = "~> 2.3.0"
    template = "~> 2.1.2"
  }
}

module "acm" {
  source = "../modules/acm"

  create_certificate = true

  environment = var.env_name
  domain_name = var.domain_name
  zone_id     = var.zone_id

  subject_alternative_names = [
    var.domain_name,
  ]

  wait_for_validation = true
}
