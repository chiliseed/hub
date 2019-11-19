resource "aws_iam_role" "ecs_task_executor" {
  name = "${var.environment}_${var.cluster}_ecs_task_executor"
  path = "/ecs/"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["ecs-tasks.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "template_file" "policy" {
  template = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
      "Action": [
        "ssm:GetParameters",
        "ssm:DescribeParameters",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF

  vars = {
    account_id = data.aws_caller_identity.current.account_id
    prefix     = var.prefix
    aws_region = data.aws_region.current.name
  }
}

resource "aws_iam_policy" "ecs_default_task" {
  name = "${var.environment}_${var.cluster}_ecs_task_executor"
  path = "/"

  policy = data.template_file.policy.rendered
}

resource "aws_iam_policy_attachment" "ecs_default_task" {
  name       = "${var.environment}_${var.cluster}_ecs_task_executor"
  roles      = [aws_iam_role.ecs_task_executor.name]
  policy_arn = aws_iam_policy.ecs_default_task.arn
}