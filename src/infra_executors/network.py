"""This module creates the vpc and it's network."""
import argparse
import os
import logging
from typing import NamedTuple

from control_center.settings import BASE_DIR
from common.crypto import get_uuid_hex

from infra_executors.utils import execute_shell_command

logger = logging.getLogger(__name__)

INFRA_DIR = os.path.join(BASE_DIR, 'infra_executors')
TERRAFORM_DIR = os.path.join(INFRA_DIR, 'terraform')
BACKENDS_DIR = os.path.join(INFRA_DIR, 'backends')
NETWORK_DIR = os.path.join(TERRAFORM_DIR, 'network')


class AwsCredentials(NamedTuple):
    access_key: str
    secret_key: str
    session_key: str
    region: str = "us-east-1"  # N.Virginia


class GeneralConfiguration(NamedTuple):
    project_name: str
    env_name: str


def create_network(
        creds: AwsCredentials,
        params: GeneralConfiguration,
        ) -> (str, None):
    """Prepare terraform config and execute it."""
    env_vars = dict(
        AWS_ACCESS_KEY_ID=creds.access_key,
        AWS_SECRET_ACCESS_KEY=creds.secret_key,
        AWS_SESSION_TOKEN=creds.session_key,
        AWS_DEFAULT_REGION=creds.region,
        TF_VAR_environment=params.env_name,
    )
    logger.info('starting')
    # configure backend
    logger.info("Initializing terraform state: %s", env_vars)
    init_cmd = [
        f'terraform init -backend-config="key={params.project_name}/network.tfstate" -no-color -reconfigure'
    ]
    init_popen = execute_shell_command(init_cmd, env_vars, NETWORK_DIR)
    if init_popen.returncode < 0:
        logger.error(
            "Failed to init terraform for backend %s", params.project_name
        )
        return
    logger.info(f"Planning terraform changes")
    plan_file = f"{get_uuid_hex()}.tfplan"
    plan_cmd = [
        f"terraform plan -detailed-exitcode -no-color -var-file=network.tfvars -out={plan_file}",
    ]
    plan_popen = execute_shell_command(plan_cmd, env_vars, NETWORK_DIR)
    # todo terraform out plan should be uploaded to s3 and saved together with exec results
    if plan_popen.returncode == 0:
        logger.info("No changes to apply")
        return

    if plan_popen.returncode == 1 or plan_popen.returncode < 0:
        logger.error("Error executing network plan")
        return

    logger.info("Got changes to apply")
    apply_cmd = [
        f"terraform apply -auto-approve -no-color {plan_file}",
    ]
    apply_resp = execute_shell_command(apply_cmd, env_vars, NETWORK_DIR)
    if apply_resp.returncode < 0:
        logger.error("Failed to apply a plan %s", plan_file)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create vpc and its network.')
    parser.add_argument('project_name', type=str,
                        help='The name of your project. Example: chiliseed')
    parser.add_argument('environment', type=str, default='develop',
                        help='The name of your environment. Example: develop')
    parser.add_argument('--aws-access-key', type=str, dest='aws_access_key')
    parser.add_argument('--aws-secret-key', type=str, dest='aws_secret_key')
    parser.add_argument('--aws-region', type=str, default='us-east-2', dest='aws_region')

    args = parser.parse_args()

    create_network(
        AwsCredentials(args.aws_access_key, args.aws_secret_key, "", args.aws_region),
        GeneralConfiguration(args.project_name, args.environment)
    )
