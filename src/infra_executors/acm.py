"""Manages AWS ACM certificate."""
import argparse
from typing import NamedTuple, Any

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)

logger = get_logger("ssl")


class SSLConfigs(NamedTuple):
    """Configs required for R53."""

    zone_id: str
    domain_name: str


def create_ssl(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    run_config: SSLConfigs,
) -> Any:
    """Create ACM certificate."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="acm",
            action="create",
            config_dir="acm",
            state_key=build_state_key(params, "acm"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def destroy_ssl(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    run_config: SSLConfigs,
) -> Any:
    """Create and apply changes in ACM."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="acm",
            action="destroy",
            config_dir="acm",
            state_key=build_state_key(params, "acm"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/destroy acm.")
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
        default="dev",
        help="The name of your environment. Example: develop",
    )
    parser.add_argument("--aws-access-key", type=str, dest="aws_access_key")
    parser.add_argument("--aws-secret-key", type=str, dest="aws_secret_key")
    parser.add_argument(
        "--aws-region", type=str, default="us-east-2", dest="aws_region"
    )
    parser.add_argument("--run-id", type=str, default=1, dest="run_id")

    args = parser.parse_args()

    aws_creds = AwsCredentials(
        args.aws_access_key, args.aws_secret_key, "", args.aws_region
    )
    common = GeneralConfiguration(
        args.project_name, args.environment, args.run_id, ""
    )
    cmd_configs = SSLConfigs(
        zone_id="Z1HXHIFC9H0X6C", domain_name="demo.chiliseed.com",
    )

    if args.cmd == "create":
        create_ssl(aws_creds, common, cmd_configs)
    if args.cmd == "destroy":
        destroy_ssl(aws_creds, common, cmd_configs)
