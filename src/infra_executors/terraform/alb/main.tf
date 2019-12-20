data "aws_subnet_ids" "private" {
  vpc_id = var.vpc_id
  tags = {
    Type = "private"
  }
}

data "aws_subnet_ids" "public" {
  vpc_id = var.vpc_id
  tags = {
    Type = "public"
  }
}

locals {
  subnet_ids = var.internal ? data.aws_subnet_ids.private.ids : data.aws_subnet_ids.public.ids
}

resource "aws_alb" "alb" {
  name               = var.alb_name
  internal           = var.internal
  load_balancer_type = "application"
  subnets            = local.subnet_ids
  security_groups    = [aws_security_group.alb.id]
  idle_timeout       = var.idle_timeout

  tags = {
    Environment = var.env_name
    Name        = var.alb_name
  }
}

resource "aws_alb_target_group" "this" {
  count = length(var.open_ports)

  name                 = var.open_ports[count.index].name
  port                 = var.open_ports[count.index].container_port
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  deregistration_delay = var.deregistration_delay

  health_check {
    path     = var.open_ports[count.index].health_check_endpoint
    protocol = var.open_ports[count.index].health_check_protocol
  }

  tags = {
    Environment = var.env_name
    Name        = var.open_ports[count.index].name
    Type        = var.internal ? "internal" : "public"
  }
}


// create https listeners only if we have ssl arn
resource "aws_alb_listener" "https" {
  count = var.ssl_certificate_arn ? aws_alb_target_group.this.count : 0

  load_balancer_arn = aws_alb.alb.id
  port              = var.open_ports[count.index].alb_port
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.this[count.index].arn
  }
}

// if we have ssl, http will redirect to https
resource "aws_alb_listener" "http-to-https" {
  count = var.ssl_certificate_arn ? aws_alb_target_group.this.count : 0

  load_balancer_arn = aws_alb.alb.id
  port              = var.open_ports[count.index].alb_port
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

// if we don't have ssl, forward to target groups
resource "aws_alb_listener" "http" {
  count = var.ssl_certificate_arn ? 0 : aws_alb_target_group.this.count

  load_balancer_arn = aws_alb.alb.id
  port              = var.open_ports[count.index].alb_port
  protocol = "HTTP"

  default_action {
    type = "forward"
    target_group_arn = aws_alb_target_group.this[count.index].arn
  }
}
