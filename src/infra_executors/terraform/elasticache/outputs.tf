output "cache_nodes_details" {
  value = aws_elasticache_cluster.this.cache_nodes
}

output "memcached_configuration_endpoint" {
  value = aws_elasticache_cluster.this.configuration_endpoint
}

output "memcached_cluster_address" {
  value = aws_elasticache_cluster.this.cluster_address
}
