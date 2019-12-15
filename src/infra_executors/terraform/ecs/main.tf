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

locals {
  cluster_name = "${var.cluster}-${var.env_name}"
}

data "aws_subnet_ids" "public" {
  vpc_id = var.vpc_id
  tags = {
    Type = "public"
  }
}

module "ecs_instances" {
  source = "../modules/ecs_instances"

  environment             = var.env_name
  cluster                 = local.cluster_name
  instance_group          = var.instance_group
  public_subnet_ids       = data.aws_subnet_ids.public.ids
  aws_ami                 = var.ecs_aws_ami
  instance_type           = var.instance_type
  max_size                = var.max_size
  min_size                = var.min_size
  desired_capacity        = var.desired_capacity
  vpc_id                  = var.vpc_id
  iam_instance_profile_id = aws_iam_instance_profile.ecs.id
  key_name                = var.ssh_key_name
  depends_id              = ""
  custom_userdata         = var.custom_userdata
  cloudwatch_prefix       = var.cloudwatch_prefix
  target_group_arns       = []
  //  target_group_arns       = module.alb.target_group_arns
}

resource "aws_ecs_cluster" "cluster" {
  name = local.cluster_name
}

module "ecs_task_executor_role" {
  source = "../modules/ecs_roles"

  environment = var.env_name
  cluster     = var.cluster
  prefix      = var.env_name
}

resource "aws_security_group_rule" "ssh" {
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = module.ecs_instances.ecs_instance_security_group_id
  type              = "ingress"
}

# todo see how and where to add ecr repositories
