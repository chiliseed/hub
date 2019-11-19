locals {
  name_prefix = "${var.identifier}-${var.environment}-"
}

module "db_parameter_group" {
  source = "../db_parameter_group"

  create = var.create_db_parameter_group

  identifier      = var.identifier
  name            = "${var.identifier}_params"
  description     = "Custom Postgres DB parameters for ${var.identifier} in ${var.environment}"
  name_prefix     = local.name_prefix
  use_name_prefix = var.use_parameter_group_name_prefix
  family          = var.params_family

  parameters  = var.parameters
  environment = var.environment
}

module "db_option_group" {
  source = "../db_option_group"

  create = var.create_db_option_group

  identifier               = var.identifier
  name_prefix              = local.name_prefix
  option_group_description = "Custom Postgres DB options for ${var.identifier} in ${var.environment}"
  engine_name              = var.engine
  major_engine_version     = var.major_engine_version

  options     = var.options
  environment = var.environment
}

module "db_subnet_group" {
  source = "../db_subnet_group"

  create      = var.create_db_subnet_group
  identifier  = var.identifier
  name_prefix = local.name_prefix
  subnet_ids  = var.subnet_ids
  environment = var.environment
}

module "db_instance" {
  source = "../db_instance"

  identifier        = var.identifier
  engine            = var.engine
  engine_version    = var.engine_version
  instance_class    = var.instance_type
  allocated_storage = var.allocated_storage
  storage_type      = var.storage_type
  storage_encrypted = var.storage_encrypted
  kms_key_id        = var.kms_key_id

  name                                = var.name
  username                            = var.username
  password                            = var.password
  port                                = var.port
  iam_database_authentication_enabled = var.iam_database_authentication_enabled

  replicate_source_db = var.replicate_source_db

  snapshot_identifier = var.snapshot_identifier

  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = module.db_subnet_group.this_db_subnet_group_id
  parameter_group_name   = module.db_parameter_group.db_parameter_group_id
  option_group_name      = module.db_option_group.this_db_option_group_id

  availability_zone   = var.availability_zone
  multi_az            = var.is_multi_az
  iops                = var.iops
  publicly_accessible = var.is_publicly_accessible

  allow_major_version_upgrade = var.allow_major_version_upgrade
  auto_minor_version_upgrade  = var.auto_minor_version_upgrade
  apply_immediately           = var.apply_immediately
  maintenance_window          = var.maintenance_window
  skip_final_snapshot         = var.skip_final_snapshot
  copy_tags_to_snapshot       = var.copy_tags_to_snapshot
  final_snapshot_identifier   = var.final_snapshot_identifier

  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window

  monitoring_interval    = var.monitoring_interval
  monitoring_role_arn    = var.monitoring_role_arn
  monitoring_role_name   = var.monitoring_role_name
  create_monitoring_role = var.create_monitoring_role

  timezone                        = var.timezone
  character_set_name              = var.character_set_name
  enabled_cloudwatch_logs_exports = var.enabled_cloudwatch_logs_exports

  timeouts = var.timeouts

  deletion_protection = var.deletion_protection

  environment = var.environment
}

