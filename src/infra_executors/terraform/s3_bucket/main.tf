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

resource "aws_s3_bucket" "statics" {
  bucket = var.bucket_name
  acl    = var.acl

  tags = {
    Name        = var.bucket_name
    Environment = var.env_name
  }

  force_destroy = true
}
