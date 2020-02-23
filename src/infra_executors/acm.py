"""Manages AWS ACM certificate."""
from typing import NamedTuple, Any

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_service_state_key
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


def create_acm(
    creds: AwsCredentials, params: GeneralConfiguration, run_config: SSLConfigs,
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
            state_key=build_service_state_key(params, "acm"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def destroy_acm(
    creds: AwsCredentials, params: GeneralConfiguration, run_config: SSLConfigs,
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
            state_key=build_service_state_key(params, "acm"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()


def get_acm_details(
    creds: AwsCredentials, params: GeneralConfiguration, run_config: SSLConfigs,
) -> Any:
    """Get ACM details."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="acm",
            action="outputs",
            config_dir="acm",
            state_key=build_service_state_key(params, "acm"),
            variables_file_name="",
        ),
    )
    return executor.get_outputs()
