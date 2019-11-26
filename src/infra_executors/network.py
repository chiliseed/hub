"""Creates the vpc and it's network."""
import argparse
import logging
import os

from common.crypto import get_uuid_hex

from infra_executors.constants import (
    AwsCredentials,
    EXEC_LOGS_DIR,
    GeneralConfiguration,
    PLANS_DIR,
    TERRAFORM_DIR,
    TERRAFORM_PLUGIN_DIR,
)
from infra_executors.utils import execute_shell_command, extract_outputs


logger = logging.getLogger(__name__)
NETWORK_DIR = os.path.join(TERRAFORM_DIR, "network")


def create_network(
    creds: AwsCredentials, params: GeneralConfiguration,
) -> (str, None):
    """Create vpc with private and subnet network, with internet access."""
    env_vars = dict(
        AWS_ACCESS_KEY_ID=creds.access_key,
        AWS_SECRET_ACCESS_KEY=creds.secret_key,
        AWS_SESSION_TOKEN=creds.session_key,
        AWS_DEFAULT_REGION=creds.region,
        TF_VAR_environment=params.env_name,
    )
    logger.info("Executing run id=%s", params.run_id)

    run_log = os.path.join(
        EXEC_LOGS_DIR, f"network_create_{params.run_id}.log"
    )

    logger.info("Initializing terraform state: %s", env_vars)

    init_cmd = [
        f"terraform init "
        f'-backend-config="key={params.project_name}/network.tfstate" '
        f"-no-color -reconfigure -plugin-dir {TERRAFORM_PLUGIN_DIR}"
    ]
    init_return_code = execute_shell_command(
        init_cmd, env_vars, NETWORK_DIR, log_to=run_log
    )
    if init_return_code != 0:
        logger.error(
            "Failed to init terraform for backend %s", params.project_name
        )
        return

    logger.info("Planning terraform changes. run_id=%s", params.run_id)
    plan_file = os.path.join(PLANS_DIR, f"network_{params.run_id}.tfplan")
    plan_cmd = [
        f"terraform plan "
        f"-detailed-exitcode "
        f"-no-color "
        f"-var-file=network.tfvars "
        f"-out={plan_file}",
    ]
    plan_return_code = execute_shell_command(
        plan_cmd, env_vars, NETWORK_DIR, log_to=run_log
    )

    if plan_return_code == 0:
        logger.info("No changes to apply")
        return

    if plan_return_code == 1 or plan_return_code < 0:
        logger.error("Error executing network plan")
        return

    logger.info("Got changes to apply")
    apply_cmd = [
        f"terraform apply -auto-approve -no-color {plan_file}",
    ]
    apply_return_code = execute_shell_command(
        apply_cmd, env_vars, NETWORK_DIR, log_to=run_log
    )
    if apply_return_code != 0:
        logger.error("Failed to apply a plan %s", plan_file)
    else:
        vpc_outputs = extract_outputs(run_log)
        logger.info("Created new vpc id=%s", vpc_outputs["vpc_id"])
        return vpc_outputs["vpc_id"]


def destroy_network(
    creds: AwsCredentials, params: GeneralConfiguration,
) -> (str, None):
    """Destroy vpc that was created with create_network from above."""
    env_vars = dict(
        AWS_ACCESS_KEY_ID=creds.access_key,
        AWS_SECRET_ACCESS_KEY=creds.secret_key,
        AWS_SESSION_TOKEN=creds.session_key,
        AWS_DEFAULT_REGION=creds.region,
        TF_VAR_environment=params.env_name,
    )
    logger.info("Executing run id=%s", params.run_id)
    run_log = os.path.join(
        EXEC_LOGS_DIR, f"network_destroy_{params.run_id}.log"
    )

    logger.info("Initializing terraform state: %s", env_vars)

    init_cmd = [
        f"terraform init "
        f'-backend-config="key={params.project_name}/network.tfstate" '
        f"-no-color "
        f"-reconfigure "
        f"-plugin-dir {TERRAFORM_PLUGIN_DIR}"
    ]
    init_return_code = execute_shell_command(
        init_cmd, env_vars, NETWORK_DIR, log_to=run_log
    )
    if init_return_code < 0:
        logger.error(
            "Failed to init terraform for backend %s", params.project_name
        )
        return

    destroy_cmd = [
        f"terraform destroy "
        f"-auto-approve "
        f"-no-color "
        f"-var-file=network.tfvars"
    ]
    destroy_return_code = execute_shell_command(
        destroy_cmd, env_vars, NETWORK_DIR, log_to=run_log
    )
    if destroy_return_code < 0:
        logger.error("Failed to destroy network. run_id=%s", params.run_id)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create/destroy vpc and its network."
    )
    parser.add_argument(
        "cmd",
        type=str,
        default="create",
        help="Sub command. One of: create/destroy",
    )
    parser.add_argument(
        "project_name",
        type=str,
        help="The name of your project. Example: chiliseed",
    )
    parser.add_argument(
        "environment",
        type=str,
        default="develop",
        help="The name of your environment. Example: develop",
    )
    parser.add_argument("--aws-access-key", type=str, dest="aws_access_key")
    parser.add_argument("--aws-secret-key", type=str, dest="aws_secret_key")
    parser.add_argument(
        "--aws-region", type=str, default="us-east-2", dest="aws_region"
    )
    parser.add_argument(
        "--run-id", type=str, default=get_uuid_hex(), dest="run_id"
    )

    args = parser.parse_args()

    aws_creds = AwsCredentials(
        args.aws_access_key, args.aws_secret_key, "", args.aws_region
    )
    common = GeneralConfiguration(
        args.project_name, args.environment, args.run_id
    )

    if args.cmd == "create":
        create_network(aws_creds, common)
    if args.cmd == "destroy":
        destroy_network(aws_creds, common)
