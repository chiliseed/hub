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

provider "aws" {}

data "aws_subnet_ids" "private" {
  vpc_id = var.vpc_id
  tags = {
    Type = "private"
  }
}

resource "aws_security_group" "cache" {
  name_prefix = "${var.env_name}-${var.identifier}-cache-"
  description = "Managed by Chiliseed."
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.env_name}-${var.identifier}-${var.engine}"
    Environment = var.env_name
  }
}

resource "aws_security_group_rule" "ingress" {
  count                    = length(var.allowed_security_groups_ids)
  type                     = "ingress"
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "TCP"
  source_security_group_id = var.allowed_security_groups_ids[count.index]
  security_group_id        = aws_security_group.cache.id
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.env_name}-${var.identifier}-cache"
  subnet_ids = data.aws_subnet_ids.private.ids
}

resource "aws_elasticache_cluster" "this" {
  cluster_id               = var.identifier
  engine                   = var.engine
  node_type                = var.instance_type
  num_cache_nodes          = var.number_of_nodes
  parameter_group_name     = var.parameter_group_name
  engine_version           = var.engine_version
  port                     = 6379
  maintenance_window       = "sun:07:00-sun:09:00"
  subnet_group_name        = aws_elasticache_subnet_group.this.name
  security_group_ids       = [aws_security_group.cache.id]
  apply_immediately        = var.apply_immediately
  snapshot_name            = "${var.env_name}-${var.identifier}-${var.engine}"
  snapshot_window          = "05:00-07:00" # daily window to take cache snapshot, for redis only
  snapshot_retention_limit = var.snapshot_retention_limit_days

  tags = {
    Name        = "${var.env_name}-${var.identifier}-${var.engine}"
    Environment = var.env_name
  }
}

