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

resource "aws_security_group" "db" {
  name_prefix = "${var.identifier}-db-"
  description = "Managed by Chiliseed. SG for db ${var.identifier}"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.env_name}-db"
    Environment = var.env_name
  }
}

resource "aws_security_group_rule" "ingress" {
  count                    = length(var.allowed_security_groups_ids)
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "TCP"
  source_security_group_id = var.allowed_security_groups_ids[count.index]
  security_group_id        = aws_security_group.db.id
}

module "master" {
  source = "../modules/db"

  identifier = var.identifier

  engine            = "postgres"
  engine_version    = "11.8"
  instance_class    = var.instance_type
  allocated_storage = var.allocated_storage
  storage_encrypted = false

  major_engine_version = "11"

  name = var.name

  username = var.username
  password = var.password
  port     = "5432"

  vpc_security_group_ids = [aws_security_group.db.id]

  maintenance_window = "Mon:00:00-Mon:03:00"
  backup_window      = "03:00-06:00"

  backup_retention_period = 1

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  # DB subnet group
  subnet_ids = data.aws_subnet_ids.private.ids

  # Snapshot name upon DB deletion
  final_snapshot_identifier = "${var.identifier}-${var.env_name}-final"

  # Database Deletion Protection
  deletion_protection = false

  # DB parameter group
  family               = "postgres11"
}


module "read-replica" {
  source = "../modules/db"

  identifier = "${var.identifier}-read"

  replicate_source_db = module.master.this_db_instance_id

  engine            = "postgres"
  engine_version    = "11.6"
  instance_class    = var.instance_type
  allocated_storage = var.allocated_storage
  storage_encrypted = false

  # Username and password must not be set for replicas
  username = ""
  password = ""
  port     = "5432"

  vpc_security_group_ids = [aws_security_group.db.id]

  maintenance_window = "Tue:00:00-Tue:03:00"
  backup_window      = "03:00-06:00"

  # disable backups to create DB faster
  backup_retention_period = 0

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  # Not allowed to specify a subnet group for replicas in the same region
  create_db_subnet_group = false

  create_db_option_group    = false
  create_db_parameter_group = false

  # Database Deletion Protection
  deletion_protection = false

  major_engine_version = "11"

  # DB parameter group
  family               = "postgres11"
}
