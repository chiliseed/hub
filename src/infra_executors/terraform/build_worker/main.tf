terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    bucket = "chiliseed-dev-terraform-states"
    region = "us-east-2"
    //    key    = "path/to.tfstate"  this will be provided on runtime
  }
  required_providers {
    aws      = "~> 2.54.0"
    null     = "~> 2.1.2"
    random   = "~> 2.2.1"
    template = "~> 2.1.2"
  }
}

data "aws_region" "current" {}

data "aws_subnet_ids" "public" {
  vpc_id = var.vpc_id
  tags = {
    Type = "public"
  }
}


data "template_file" "init" {
  template = file("${path.module}/build_worker_setup.tpl")
  vars = {
    region                = data.aws_region.current.name
    aws_access_key_id     = var.aws_access_key_id
    aws_access_key_secret = var.aws_access_key_secret
    env_name              = var.env_name
    code_version          = var.code_version
    dockerfile            = var.dockerfile
    dockerfile_target     = var.dockerfile_target
    service_name          = var.service_name
    ecr_url               = var.ecr_url
    build_tool_version    = var.build_tool_version
  }
}

resource "aws_spot_instance_request" "build-worker" {
  ami                         = var.worker_ami
  spot_price                  = var.spot_max_price
  spot_type                   = "one-time"
  block_duration_minutes      = 60 # must be a multiple of 60 (60, 120, 180, 240, 300, or 360)
  instance_type               = "c4.large"
  wait_for_fulfillment        = true
  valid_until                 = var.valid_until
  key_name                    = var.ssh_key_name
  user_data                   = data.template_file.init.rendered
  vpc_security_group_ids      = [aws_security_group.build-worker.id]
  subnet_id                   = sort(data.aws_subnet_ids.public.ids)[0]
  associate_public_ip_address = true
  monitoring                  = true

  timeouts {
    create = "2m"
    delete = "2m"
  }

  tags = {
    Note      = "Managed by Chiliseed"
    Name      = "build-worker-${var.service_name}"
    Component = "DevOps"
    Service   = var.service_name
  }
}

resource "random_string" "random" {
  length = 8
  special = false
  lower = true
}

resource "aws_security_group" "build-worker" {
  vpc_id      = var.vpc_id
  name = "build-worker-${var.service_name}-${random_string.random.result}"
  description = "Managed by Chiliseed"

  ingress {
    from_port   = 22
    protocol    = "tcp"
    to_port     = 22
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.env_name
    Service     = var.service_name
    Component   = "ci/cd"
  }
}
