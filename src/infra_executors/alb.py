"""Manages ALB component."""
import argparse
from typing import Any, List, NamedTuple, NewType, Optional

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)

logger = get_logger("alb")

Protocol = NewType("Protocol", str)

TCP = Protocol("TCP")
UDP = Protocol("UDP")
TLS = Protocol("TLS")
TCP_UDP = Protocol("TCP_UDP")
HTTP = Protocol("HTTP")
HTTPS = Protocol("HTTPS")


class OpenPort(NamedTuple):
    """Describes open ports configuration."""

    name: str
    container_port: int
    alb_port_http: int
    alb_port_https: int
    health_check_endpoint: str
    health_check_protocol: Protocol


class ALBConfigs(NamedTuple):
    """Configures alb."""

    alb_name: str
    ssl_certificate_arn: Optional[str]
    open_ports: List[OpenPort]

    internal: bool = False
    idle_timeout: int = 60  # in seconds
    deregistration_delay: int = 300  # in seconds


def create_alb(
    creds: AwsCredentials, params: GeneralConfiguration, alb_conf: ALBConfigs
) -> Any:
    """Create and manage alb."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=alb_conf,
        executor_configs=ExecutorConfiguration(
            name="alb",
            action="create",
            config_dir="alb",
            state_key=build_state_key(params, "alb"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def get_alb_details(
    creds: AwsCredentials, params: GeneralConfiguration, alb_conf: ALBConfigs
) -> Any:
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=alb_conf,
        executor_configs=ExecutorConfiguration(
            name="alb",
            action="outputs",
            config_dir="alb",
            state_key=build_state_key(params, "alb"),
            variables_file_name="",
        ),
    )
    return executor.get_outputs()


def destroy_alb(
    creds: AwsCredentials, params: GeneralConfiguration, alb_conf: ALBConfigs
) -> Any:
    """Destroy alb."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=alb_conf,
        executor_configs=ExecutorConfiguration(
            name="alb",
            action="destroy",
            config_dir="alb",
            state_key=build_state_key(params, "alb"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create/destroy alb in the provides vpc."
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
    parser.add_argument(
        "vpc_id",
        type=str,
        help="The id of the vpc. Example: vpc-0c5b94e64b709fa24",
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
        args.project_name, args.environment, args.run_id, args.vpc_id
    )
    # First run
    # cmd_configs = ALBConfigs(
    #     alb_name=f"{common.project_name}-alb",
    #     ssl_certificate_arn=None,
    #     open_ports=[
    #         OpenPort(
    #             name=f"{common.project_name}-api",
    #             container_port=7878,
    #             alb_port_https=443,
    #             alb_port_http=80,
    #             health_check_endpoint="/health/check",
    #             health_check_protocol=HTTP,
    #         ),
    #     ],
    # )
    cmd_configs = ALBConfigs(
        alb_name=f"{common.project_name}-alb",
        ssl_certificate_arn="arn:aws:acm:us-east-2:576465297898:certificate/cc99d5a3-ad29-419d-a23c-5d1c3cfd094a",  # noqa: E501
        open_ports=[
            OpenPort(
                name=f"{common.project_name}-api",
                container_port=7878,
                alb_port_https=443,
                alb_port_http=80,
                health_check_endpoint="/health/check",
                health_check_protocol=HTTP,
            ),
        ],
    )

    if args.cmd == "create":
        create_alb(aws_creds, common, cmd_configs)
    if args.cmd == "destroy":
        destroy_alb(aws_creds, common, cmd_configs)
