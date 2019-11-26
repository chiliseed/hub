data "aws_subnet_ids" "public" {
  vpc_id = var.vpc_id
  tags = {
    Type = "public"
  }
}

resource "aws_security_group" "db" {
  name        = "${var.environment}_db"
  description = "Used in ${var.environment}"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.environment}_db"
    Environment = var.environment
  }
}

module "master" {
  source = "../modules/db"

  identifier = var.identifier

  engine            = "postgres"
  engine_version    = "11.2"
  instance_type     = var.instance_type
  allocated_storage = var.allocated_storage
  storage_encrypted = false

  major_engine_version = "11"

  name        = var.name
  name_prefix = var.environment

  username = var.username
  password = var.password
  port     = "5432"

  security_group_ids = [aws_security_group.db.id]

  maintenance_window = "Mon:00:00-Mon:03:00"
  backup_window      = "03:00-06:00"

  backup_retention_period = 1

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  # DB subnet group
  subnet_ids = data.aws_subnet_ids.public

  # Snapshot name upon DB deletion
  final_snapshot_identifier = "${var.identifier}-${var.environment}-final"

  # Database Deletion Protection
  deletion_protection = false

  environment = var.environment

  create_db_option_group    = true
  create_db_parameter_group = false
}


module "read-replica" {
  source = "../modules/db"

  identifier = "${var.identifier}-read"

  replicate_source_db = module.master.instance_id

  engine            = "postgres"
  engine_version    = "11.2"
  instance_type     = var.instance_type
  allocated_storage = var.allocated_storage
  storage_encrypted = false

  # Username and password must not be set for replicas
  username = ""
  password = ""
  port     = "5432"

  security_group_ids = [aws_security_group.db.id]

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

  environment = var.environment

  # Don't need to specify for replica, will be taken from master
  major_engine_version = "11"
}
