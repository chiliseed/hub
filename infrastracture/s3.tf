//locals {
//  states_bucket_name = "chiliseed-terraform-states-${var.environment}"
//  runs = "chiliseed-infrastructure-runs-${var.environment}"
//}
//
//resource "aws_s3_bucket" "infra_buckets" {
//  bucket = local.states_bucket_name
//  acl    = "private"
//
//  tags = {
//    Name        = local.states_bucket_name
//    Environment = var.environment
//  }
//}
//
//resource "aws_s3_bucket" "runs" {
//  bucket = local.runs
//  acl    = "private"
//
//  tags = {
//    Name        = local.runs
//    Environment = var.environment
//  }
//}
//
