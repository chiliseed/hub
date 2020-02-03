"""Manages Route53 resource."""
import argparse
from typing import Any, List, NamedTuple

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)

logger = get_logger("r53-infra-executor")


class CnameSubDomain(NamedTuple):
    """Subdomain configuration."""

    subdomain: str
    route_to: str


class Route53Configuration(NamedTuple):
    """Route53 configs."""

    domain: str
    cname_subdomains: List[CnameSubDomain]


def create_route53(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    run_config: Route53Configuration,
) -> Any:
    """Create and apply changes in route 53."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="route53",
            action="create",
            config_dir="route53",
            state_key=build_state_key(params, "route53"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def destroy_route53(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    run_config: Route53Configuration,
) -> Any:
    """Create and apply changes in route 53."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="route53",
            action="destroy",
            config_dir="route53",
            state_key=build_state_key(params, "route53"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()


def get_r53_details(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    run_config: Route53Configuration,
) -> Any:
    """Get route 53 details."""
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="route53",
            action="outputs",
            config_dir="route53",
            state_key=build_state_key(params, "route53"),
            variables_file_name="",
        ),
    )
    return executor.get_outputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/destroy route 53 hosted zone.")
    parser.add_argument(
        "cmd", type=str, default="create", help="Sub command. One of: create/destroy",
    )
    parser.add_argument(
        "project_name", type=str, help="The name of your project. Example: chiliseed",
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
    common = GeneralConfiguration(args.project_name, args.environment, args.run_id, "")
    cmd_configs = Route53Configuration(
        domain="chiliseed.com",
        cname_subdomains=[
            CnameSubDomain("demo", "demo-alb-1852262830.us-east-2.elb.amazonaws.com")
        ],
    )

    if args.cmd == "create":
        create_route53(aws_creds, common, cmd_configs)
    if args.cmd == "destroy":
        destroy_route53(aws_creds, common, cmd_configs)
