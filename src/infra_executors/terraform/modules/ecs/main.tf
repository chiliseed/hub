module "ecs_instances" {
  source = "../ecs_instances"

  environment             = var.environment
  cluster                 = var.cluster
  instance_group          = var.instance_group
  public_subnet_ids       = var.public_subnet_ids
  aws_ami                 = var.ecs_aws_ami
  instance_type           = var.instance_type
  max_size                = var.max_size
  min_size                = var.min_size
  desired_capacity        = var.desired_capacity
  vpc_id                  = var.vpc_id
  iam_instance_profile_id = var.ecs_iam_instance_role_id
  key_name                = var.key_name
  depends_id              = ""
  custom_userdata         = var.custom_userdata
  cloudwatch_prefix       = var.cloudwatch_prefix
  target_group_arns = []
//  target_group_arns       = module.alb.target_group_arns
}

resource "aws_ecs_cluster" "cluster" {
  name = "${var.environment}-${var.cluster}"
}

resource "aws_security_group_rule" "instance_to_db" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "TCP"
  source_security_group_id = module.ecs_instances.ecs_instance_security_group_id
  security_group_id        = var.db_security_group_id
}

module "ecs_task_executor_role" {
  source = "../ecs_roles"

  environment = var.environment
  cluster     = var.cluster
  prefix      = var.environment
}
