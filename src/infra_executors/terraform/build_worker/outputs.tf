output "spot_request_id" {
  value = aws_spot_instance_request.build-worker.id
}

output "spot_bid_status" {
  value = aws_spot_instance_request.build-worker.spot_bid_status
}

output "instance_id" {
  value = aws_spot_instance_request.build-worker.spot_instance_id
}

output "instance_public_ip" {
  value = aws_spot_instance_request.build-worker.public_ip
}

output "instance_private_ip" {
  value = aws_spot_instance_request.build-worker.private_ip
}

