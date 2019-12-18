terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    bucket = "chiliseed-dev-terraform-states"
    region = "us-east-2"
    //    key    = "path/to.tfstate"  this will be provided on runtime
  }
  required_providers {
    aws      = "~> 2.39.0"
    null     = "~> 2.1.2"
    random   = "~> 2.2.1"
    template = "~> 2.1.2"
  }
}

locals {cnames = split(",", var.cname_subdomains)}

resource "aws_route53_zone" "primary" {
  name    = var.domain
  comment = "Managed by Chiliseed"

  tags = {
    Environment = var.enviroment
  }
}

resource "aws_route53_record" "subdomains" {
  count   = length(local.cnames)
  allow_overwrite = true
  name    = "${local.cnames[count.index]}.${var.domain}"
  type    = "CNAME"
  ttl     = "300"
  zone_id = aws_route53_zone.primary.id
}
