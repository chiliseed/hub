resource "aws_iam_user" "ecs_deployer" {
  name = "ecs_deployer"
  path = "/ecs/"
}

resource "aws_iam_user_policy" "ecs_deployer_policy" {
  name = "ecs_deployer_policy"
  user = aws_iam_user.ecs_deployer.name

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecs:RunTask",
                "ecs:StopTask",
                "ecs:ListTasks",
                "ecs:RegisterTaskDefinition",
                "ecs:ListTaskDefinitions",
                "ecs:CreateService",
                "ecs:UpdateService",
                "ecs:DescribeServices",
                "ecs:ListServices",
                "ecs:ListAccountSettings",
                "ecs:DescribeTasks",
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:GetRepositoryPolicy",
                "ecr:DescribeRepositories",
                "ecr:ListImages",
                "ecr:DescribeImages",
                "ecr:BatchGetImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:PutImage",
                "logs:CreateLogGroup",
                "s3:PutObject",
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:DeleteObject",
                "s3:PutObjectAcl",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:ListAllMyBuckets",
                "cloudfront:CreateInvalidation",
                "ec2:*",
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

resource "aws_iam_access_key" "ecs_deployer" {
  user = aws_iam_user.ecs_deployer.name
}
