#!/usr/bin/env bash

echo "AWS_DEFAULT_REGION=${region}" >> /etc/environment
echo "AWS_ACCESS_KEY_ID=${aws_access_key_id}" >> /etc/environment
echo "AWS_SECRET_ACCESS_KEY=${aws_access_key_secret}" >> /etc/environment
echo "CHILISEED_ENV=${env_name}" >> /etc/environment
echo "CHILISEED_VERSION=${code_version}" >> /etc/environment
echo "CHILISEED_DOCKERFILE_TARGET=${dockerfile_target}" >> /etc/environment
echo "CHILISEED_DOCKERFILE=${dockerfile}" >> /etc/environment
echo "CHILISEED_SERVICE_NAME=${service_name}" >> /etc/environment
echo "CHILISEED_ECR_URL=${ecr_url}" >> /etc/environment
echo "CHILISEED_LOG=DEBUG" >> /etc/environment

curl -O https://chiliseed-tools.s3.us-east-2.amazonaws.com/chiliseed-build-worker-0.1.0.tar.gz
tar -xvzf chiliseed-build-worker-${build_tool_version}.tar.gz -C /home/ubuntu
