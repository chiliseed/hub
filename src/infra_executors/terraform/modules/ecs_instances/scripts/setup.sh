#!/usr/bin/env bash

# ECS config
${ecs_config}
{
  echo "ECS_CLUSTER=${cluster_name}"
} >> /etc/ecs/ecs.config
