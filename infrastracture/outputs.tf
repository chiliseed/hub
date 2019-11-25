output "executor_access_key" {
  value = aws_iam_access_key.executor.id
}

output "executor_secret_key" {
  value = aws_iam_access_key.executor.secret
}
