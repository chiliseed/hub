locals {
  description = coalesce(var.parameter_group_description, "Database parameter group for ${var.identifier}")
}

resource "aws_db_parameter_group" "this_no_prefix" {
  count = var.create_db_parameter_group && false == var.use_parameter_group_name_prefix ? 1 : 0

  name        = var.parameter_group_name
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

  tags = merge(
    var.tags,
    {
      "Name" = format("%s", var.name)
    },
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_parameter_group" "this" {
  count = var.create_db_parameter_group && var.use_parameter_group_name_prefix ? 1 : 0

  name_prefix = "${var.identifier}-"
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

  tags = merge(
    var.tags,
    {
      "Name" = format("%s", var.identifier)
    },
  )

  lifecycle {
    create_before_destroy = true
  }
}
