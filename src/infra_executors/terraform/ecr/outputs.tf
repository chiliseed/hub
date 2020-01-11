output "repositories_arn" {
  value = aws_ecr_repository.repos.*.arn
}

output "repositories_names" {
  value = aws_ecr_repository.repos.*.name
}

output "repositories_urls" {
  value = aws_ecr_repository.repos.*.repository_url
}
