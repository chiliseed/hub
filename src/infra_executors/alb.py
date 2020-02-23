"""Manages ALB component."""
from typing import Any, List, NamedTuple, NewType

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_project_state_key
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
    ssl_certificate_arn: str


class ALBConfigs(NamedTuple):
    """Configures alb."""

    alb_name: str
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
            state_key=build_project_state_key(params, "alb"),
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
            state_key=build_project_state_key(params, "alb"),
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
            state_key=build_project_state_key(params, "alb"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()
