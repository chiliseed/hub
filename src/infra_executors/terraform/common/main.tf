terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    # todo this should be created based on user input as separate backend.hcl file and provided to terraform init --backend-config=
//    bucket = "flytrex-terraform-states"
//    region = "us-east-2"
//    key    = "delivery_service/common-infra.tfstate"
  }
}

provider "aws" {
  # todo use region provided via enviroment variables.
//  region = "us-west-2"
}

module "network" {
  source               = "../modules/network"
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  depends_id           = ""
}

module "ecs_deployer" {
  source = "../modules/deployer_user"
}

resource "aws_route53_zone" "primary" {
  name = var.domain
}
