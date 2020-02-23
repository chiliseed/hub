"""Manages Route53 resource."""
from typing import Any, List, NamedTuple

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_environment_state_key
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
            state_key=build_environment_state_key(params, "route53"),
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
            state_key=build_environment_state_key(params, "route53"),
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
            state_key=build_environment_state_key(params, "route53"),
            variables_file_name="",
        ),
    )
    return executor.get_outputs()
