#!/usr/bin/env bash

echo "AWS_DEFAULT_REGION=${region}" >> /etc/environment
echo "AWS_ACCESS_KEY_ID=${aws_access_key_id}" >> /etc/environment
echo "AWS_SECRET_ACCESS_KEY=${aws_access_key_secret}" >> /etc/environment
echo "CHILISEED_ENV=${env_name}" >> /etc/environment
echo "CHILISEED_VERSION=${code_version}" >> /etc/environment
echo "DOCKERFILE_TARGET=${dockerfile_target}" >> /etc/environment
echo "CHILISEED_SERVICE_NAME=${service_name}" >> /etc/environment
echo "CHILISEED_ECR_URL=${ecr_url}" >> /etc/environment
