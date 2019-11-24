terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    bucket = "chiliseed-dev-terraform-states"
    region = "us-east-2"
//    key    = "delivery_service/liberty.tfstate"  this will be provided on runtime
  }
  required_providers {
    aws = "~> 2.0"
    null = "~> 2.0"
    random = "~> 2.0"
  }
}

provider "aws" {}

module "network" {
  source               = "../modules/network"
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  depends_id           = ""
}
