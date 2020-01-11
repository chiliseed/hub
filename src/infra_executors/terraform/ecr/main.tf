terraform {
  required_version = ">=0.12.1"
  backend "s3" {
    bucket = "chiliseed-dev-terraform-states"
    region = "us-east-2"
    //    key    = "path/to.tfstate"  this will be provided on runtime
  }
  required_providers {
    aws      = "~> 2.39.0"
    null     = "~> 2.1.2"
    random   = "~> 2.2.1"
    template = "~> 2.1.2"
  }
}

resource "aws_ecr_repository" "repos" {
  count = length(var.repositories)

  name = "${var.env_name}/${var.repositories[count.index]}"

  image_tag_mutability = "IMMUTABLE"
}

resource "aws_ecr_lifecycle_policy" "cleanup_policy" {
  count = length(aws_ecr_repository.repos)
  repository = aws_ecr_repository.repos[count.index].name

  policy     = <<EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 100 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 100
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF
}
