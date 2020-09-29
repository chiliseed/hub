locals {
  db_subnet_group_name          = var.db_subnet_group_name != "" ? var.db_subnet_group_name : element(concat(aws_db_subnet_group.this.*.id, [""]), 0)
  enable_create_db_subnet_group = var.db_subnet_group_name == "" ? var.create_db_subnet_group : false

  parameter_group_name    = var.parameter_group_name != "" ? var.parameter_group_name : var.identifier
  parameter_group_name_id = var.parameter_group_name != "" ? var.parameter_group_name : element(concat(aws_db_parameter_group.this.*.id, aws_db_parameter_group.this_no_prefix.*.id, [""]), 0)

  option_group_name             = var.option_group_name != "" ? var.option_group_name : element(concat(aws_db_option_group.this.*.id, [""]), 0)
  enable_create_db_option_group = var.create_db_option_group ? true : var.option_group_name == "" && var.engine != "postgres"
}
