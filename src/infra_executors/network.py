"""Creates the vpc and it's network."""
import argparse
from typing import Mapping

from common.crypto import get_uuid_hex

from infra_executors.constants import (
    AwsCredentials,
    GeneralConfiguration,
)
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)


logger = get_logger(__name__)


def create_network(
    creds: AwsCredentials, params: GeneralConfiguration,
) -> Mapping[str, str]:
    """Create vpc with private and subnet network, with internet access."""
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="network",
            action="create",
            config_dir="network",
            state_key=build_state_key(params, "network"),
            variables_file_name="network.tfvars",
        ),
    )
    return executor.execute_apply()


def destroy_network(
    creds: AwsCredentials, params: GeneralConfiguration,
) -> None:
    """Destroy vpc that was created with create_network from above."""
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="network",
            action="destroy",
            config_dir="network",
            state_key=build_state_key(params, "network"),
            variables_file_name="network.tfvars",
        ),
    )
    return executor.execute_destroy()


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
