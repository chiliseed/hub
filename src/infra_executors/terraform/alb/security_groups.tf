locals {
  ingress       = "ingress"
  egress        = "egress"
  tcp           = "TCP"
  anywhere_cidr = "0.0.0.0/0"
}

resource "aws_security_group" "alb" {
  name        = "${var.env_name}_${var.alb_name}"
  description = "Used in ${var.env_name}"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.env_name}_${var.alb_name}"
    Environment = var.env_name
    Project     = var.project_name
  }
}

resource "aws_security_group_rule" "outbound_internet_access" {
  type              = local.egress
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = [local.anywhere_cidr]
  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "listeners-https" {
  count = length(var.open_ports)

  from_port         = var.open_ports[count.index].alb_port_https
  to_port           = var.open_ports[count.index].alb_port_https
  protocol          = local.tcp
  security_group_id = aws_security_group.alb.id
  type              = local.ingress
  cidr_blocks       = [local.anywhere_cidr]
}

resource "aws_security_group_rule" "listeners-http" {
  count = length(var.open_ports)

  from_port         = var.open_ports[count.index].alb_port_http
  to_port           = var.open_ports[count.index].alb_port_http
  protocol          = local.tcp
  security_group_id = aws_security_group.alb.id
  type              = local.ingress
  cidr_blocks       = [local.anywhere_cidr]
}
