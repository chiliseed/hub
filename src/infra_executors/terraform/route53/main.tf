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

resource "aws_route53_zone" "primary" {
  name    = var.domain
  comment = "Managed by Chiliseed"

  tags = {
    Environment = var.env_name
  }
}

resource "aws_route53_record" "subdomains" {
  count   = length(var.cname_subdomains)
  allow_overwrite = true
  name    = "${var.cname_subdomains[count.index].subdomain}.${var.domain}"
  type    = "CNAME"
  ttl     = "300"
  zone_id = aws_route53_zone.primary.id
  records = [var.cname_subdomains[count.index].route_to]
}
