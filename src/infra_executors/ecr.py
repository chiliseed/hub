"""Manages ecr repos."""
from typing import Any, List, NamedTuple

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_service_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)

logger = get_logger("ecr")


class ECRConfigs(NamedTuple):
    """List of repositories to create."""

    repositories: List[str]


def create_ecr(
    creds: AwsCredentials, params: GeneralConfiguration, ecr_conf: ECRConfigs
) -> Any:
    """Create and manage alb."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=ecr_conf,
        executor_configs=ExecutorConfiguration(
            name="ecr",
            action="create",
            config_dir="ecr",
            state_key=build_service_state_key(params, "ecr"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def destroy_ecr(
    creds: AwsCredentials, params: GeneralConfiguration, ecr_conf: ECRConfigs
) -> Any:
    """Destroy alb."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=ecr_conf,
        executor_configs=ExecutorConfiguration(
            name="ecr",
            action="destroy",
            config_dir="ecr",
            state_key=build_service_state_key(params, "ecr"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()
