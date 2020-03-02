terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    bucket = "chiliseed-dev-terraform-states"
    region = "us-east-2"
    //    key    = "path/to.tfstate"  this will be provided on runtime
  }
  required_providers {
    aws      = "~> 2.51.0"
    null     = "~> 2.1.2"
    random   = "~> 2.2.1"
    template = "~> 2.1.2"
  }
}

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

# Generate a random string to add it to the name of the Target Group
resource "random_string" "alb_prefix" {
  length  = 4
  upper   = false
  special = false
}

resource "aws_alb_target_group" "this" {
  count = length(var.open_ports)

  name                 = "${var.open_ports[count.index].name}-${random_string.alb_prefix.result}"
  port                 = var.open_ports[count.index].container_port
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  deregistration_delay = var.deregistration_delay

  lifecycle {
    // we must create before destroy because of listeners that are connected to
    // target groups
    create_before_destroy = true
  }

  health_check {
    path     = var.open_ports[count.index].health_check_endpoint
    protocol = var.open_ports[count.index].health_check_protocol
    port = "traffic-port"  // setting up dynamic ports
  }

  tags = {
    Environment = var.env_name
    Name        = var.open_ports[count.index].name
    Type        = var.internal ? "internal" : "public"
  }
}


// create https listeners only if we have ssl arn
resource "aws_alb_listener" "https" {
  count = length(aws_alb_target_group.this)

  load_balancer_arn = aws_alb.alb.id
  port              = var.open_ports[count.index].alb_port_https
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.open_ports[count.index].ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.this[count.index].arn
  }
}

// if we have ssl, http will redirect to https
resource "aws_alb_listener" "http-to-https" {
  count = length(aws_alb_target_group.this)

  load_balancer_arn = aws_alb.alb.id
  port              = var.open_ports[count.index].alb_port_http
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
//resource "aws_alb_listener" "http" {
//  count = var.open_ports[count.index].ssl_certificate_arn == "" ? length(aws_alb_target_group.this) : 0
//
//  load_balancer_arn = aws_alb.alb.id
//  port              = var.open_ports[count.index].alb_port_http
//  protocol = "HTTP"
//
//  default_action {
//    type = "forward"
//    target_group_arn = aws_alb_target_group.this[count.index].arn
//  }
//}
