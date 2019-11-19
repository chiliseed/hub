resource "aws_route53_record" "subdomain" {
  zone_id = var.route_53_zone_id
  name = "${var.subdomain}.${var.domain}"
  type    = "CNAME"
  ttl     = "60"
  records = [module.alb.public_dns]
}


module "alb" {
  source = "../alb"

  environment       = var.environment
  alb_name          = "${var.environment}-${var.cluster}"
  vpc_id            = var.vpc_id
  public_subnet_ids = var.public_subnet_ids
  health_check_path = var.health_check_path
  idle_timeout      = var.load_balancer_idle_timeout

  ssl_certificate_arn = var.ssl_certificate_arn
}

resource "aws_security_group_rule" "alb_to_ecs" {
  type                     = "ingress"
  from_port                = 32768
  to_port                  = 61000
  protocol                 = "TCP"
  source_security_group_id = module.alb.alb_security_group_id
  security_group_id        = module.ecs_instances.ecs_instance_security_group_id
}
