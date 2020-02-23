import os
from typing import NamedTuple

from django.conf import settings

INFRA_DIR = os.path.join(settings.BASE_DIR, "infra_executors")
TERRAFORM_DIR = os.path.join(INFRA_DIR, "terraform")
EXEC_LOGS_DIR = os.path.join(INFRA_DIR, "exec_logs")
TERRAFORM_PLUGIN_DIR = os.path.join("/root", ".terraform.d", "plugins", "linux_amd64")
PLANS_DIR = os.path.join(INFRA_DIR, "terraform_plans")
KEYS_DIR = os.path.join(INFRA_DIR, "key_pairs")


class AwsCredentials(NamedTuple):
    """AWS credentials configs."""

    access_key: str
    secret_key: str
    session_key: str
    region: str = "us-east-2"  # Ohio


class GeneralConfiguration(NamedTuple):
    """Common execution configs."""

    organization_id: str
    env_id: str
    project_id: str
    service_id: str
    env_name: str
    env_slug: str
    project_name: str
    run_id: str
    vpc_id: str = ""
