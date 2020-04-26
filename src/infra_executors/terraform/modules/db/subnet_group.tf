resource "aws_db_subnet_group" "this" {
  count = var.create_db_subnet_group ? 1 : 0

  name_prefix = "${var.identifier}-"
  description = "Database subnet group for ${var.identifier}"
  subnet_ids  = var.subnet_ids

  tags = merge(
    var.tags,
    {
      "Name" = format("%s", var.identifier)
    },
  )
}
