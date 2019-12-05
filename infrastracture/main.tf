terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    bucket = "chiliseed-system-terraform-states"
    region = "us-east-2"
    key    = "dev.tfstate"
  }
  required_providers {
    aws = "~> 2.39.0"
    null = "~> 2.1.2"
    random = "~> 2.2.1"
  }
}

provider "aws" {
  region = "us-east-2"
}
