resource "aws_alb_target_group" "mission_manager" {
  name                 = "${var.environment}-mission-manager"
  port                 = 37771
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  deregistration_delay = var.deregistration_delay

  health_check {
    path     = var.health_check_path
    protocol = "HTTP"
  }

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-test-frontend"
  }
}

resource "aws_alb_target_group" "test_frontend" {
  name                 = "${var.environment}-test-fe"
  port                 = 39000
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  deregistration_delay = var.deregistration_delay

  health_check {
    path     = "/"
    protocol = "HTTP"
  }

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-test-frontend"
  }
}

resource "aws_alb_target_group" "dashboard_api" {
  name                 = "${var.environment}-dashboard-api"
  port                 = 38000
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  deregistration_delay = var.deregistration_delay

  health_check {
    path     = var.health_check_path
    protocol = "HTTP"
  }

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-dashboard-backend"
  }
}

resource "aws_alb_target_group" "dashboard_api_external" {
  name                 = "${var.environment}-dashboard-external"
  port                 = 38001
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  deregistration_delay = var.deregistration_delay

  health_check {
    path     = var.health_check_path
    protocol = "HTTP"
  }

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-dashboard-backend"
  }
}

resource "aws_alb" "alb" {
  name                = var.alb_name
  internal            = false
  load_balancer_type  = "application"
  subnets             = flatten([var.public_subnet_ids])
  security_groups     = [aws_security_group.alb.id]
  idle_timeout        = var.idle_timeout

  tags = {
    Environment       = var.environment
    Name              = var.alb_name
  }
}

resource "aws_alb_listener" "https" {
  load_balancer_arn = aws_alb.alb.id
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    target_group_arn = aws_alb_target_group.dashboard_api_external.id
    type             = "forward"
  }
}

resource "aws_alb_listener" "https-dashboard-api" {
  load_balancer_arn = aws_alb.alb.id
  port              = "8000"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    target_group_arn = aws_alb_target_group.dashboard_api.id
    type             = "forward"
  }
}

resource "aws_alb_listener" "https-mission-manager" {
  load_balancer_arn = aws_alb.alb.id
  port              = "7771"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    target_group_arn = aws_alb_target_group.mission_manager.id
    type             = "forward"
  }
}

resource "aws_alb_listener" "https-test_frontend" {
  load_balancer_arn = aws_alb.alb.id
  port              = "9000"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    target_group_arn = aws_alb_target_group.test_frontend.id
    type             = "forward"
  }
}

resource "aws_alb_listener" "http" {
  load_balancer_arn = aws_alb.alb.id
  port              = "80"
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

resource "aws_security_group" "alb" {
  name   = "${var.alb_name}_alb"
  vpc_id = var.vpc_id

  tags = {
    Environment = var.environment
    Name        = "${var.alb_name}-alb-sg"
  }
}

resource "aws_security_group_rule" "https_from_anywhere" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "TCP"
  cidr_blocks       = [var.allow_cidr_block]
  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "test_frontend_https_from_anywhere" {
  type              = "ingress"
  from_port         = 9000
  to_port           = 9000
  protocol          = "TCP"
  cidr_blocks       = [var.allow_cidr_block]
  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "dashboard-api" {
  type              = "ingress"
  from_port         = 8000
  to_port           = 8000
  protocol          = "TCP"
  cidr_blocks       = [var.allow_cidr_block]
  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "mission-manager" {
  type              = "ingress"
  from_port         = 7771
  to_port           = 7771
  protocol          = "TCP"
  cidr_blocks       = [var.allow_cidr_block]
  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "outbound_internet_access" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.alb.id
}
