output "vpc_id" {
  value = module.network.vpc_id
}

output "private_subnet_ids" {
  value = flatten(module.network.private_subnet_ids)
}

output "public_subnet_ids" {
  value = flatten(module.network.public_subnet_ids)
}

output "depends_id" {
  value = module.network.depends_id
}
