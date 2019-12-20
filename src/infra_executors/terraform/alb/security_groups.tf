locals {
  ingress = "ingress"
  egress = "egress"
  tcp = "TCP"
  anywhere_cidr = "0.0.0.0/0"
}

resource "aws_security_group" "alb" {
  name        = "${var.env_name}_${var.alb_name}_alb"
  description = "Used in ${var.env_name}"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.env_name}_${var.alb_name}_alb"
    Environment = var.env_name
  }
}
//
//resource "aws_security_group_rule" "https_from_anywhere" {
//  type              = local.ingress
//  from_port         = 443
//  to_port           = 443
//  protocol          = local.tcp
//  cidr_blocks       = [local.anywhere_cidr]
//  security_group_id = aws_security_group.alb.id
//}
//
//resource "aws_security_group_rule" "http_from_anywhere" {
//  type              = local.ingress
//  from_port         = 80
//  to_port           = 80
//  protocol          = local.tcp
//  cidr_blocks       = [local.anywhere_cidr]
//  security_group_id = aws_security_group.alb.id
//}

resource "aws_security_group_rule" "outbound_internet_access" {
  type              = local.egress
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = [local.anywhere_cidr]
  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "listeners" {
  count = length(var.open_ports)

  from_port         = var.open_ports[count.index].alb_port
  to_port           = var.open_ports[count.index].alb_port
  protocol          = local.tcp
  security_group_id = aws_security_group.alb.id
  type              = local.ingress
  cidr_blocks = [local.anywhere_cidr]
}
