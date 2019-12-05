resource "aws_iam_user" "executor" {
  name = "infra_executor"
  path = "/system/"
}

resource "aws_iam_user_policy" "ecs_deployer_policy" {
  name = "infra_executor_policy"
  user = aws_iam_user.executor.name

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation",
                "ec2:*",
                "ecs:*",
                "ecr:*",
                "iam:GetRole",
                "iam:ListAttachedRolePolicies",
                "iam:CreateServiceLinkedRole",
                "logs:CreateLogGroup",
                "rds:*",
                "s3:*",
                "ssm:GetParameters",
                "ssm:DescribeParameters"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": ["iam:PassRole"],
            "Resource": "arn:aws:iam::*:role/ecs/*"
        }
    ]
}
EOF
}

resource "aws_iam_access_key" "executor" {
  user = aws_iam_user.executor.name
}
