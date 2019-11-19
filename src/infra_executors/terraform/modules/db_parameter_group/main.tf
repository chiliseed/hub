locals {
  description = coalesce(var.description, "Database parameter group for ${var.identifier}")
}

resource "aws_db_parameter_group" "db_params" {

  name        = var.name
  description = local.description
  family      = var.family

  tags = {
    Name = format("%s", var.identifier),
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }

  count = var.create && false == var.use_name_prefix ? 1 : 0

  dynamic "parameter" {
    for_each = var.parameters
    content {
      name         = parameter.value.name
      value        = parameter.value.value
      apply_method = lookup(parameter.value, "apply_method", null)
    }
  }
}

resource "aws_db_parameter_group" "prefixed_db_params" {

  count = var.create && var.use_name_prefix ? 1 : 0

  name_prefix = var.name_prefix
  description = local.description
  family      = var.family

  dynamic "parameter" {
    for_each = var.parameters
    content {
      name         = parameter.value.name
      value        = parameter.value.value
      apply_method = lookup(parameter.value, "apply_method", null)
    }
  }

  tags = {
    Name = format("%s", var.identifier),
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}
