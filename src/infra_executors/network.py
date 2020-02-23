"""Creates the vpc and it's network."""
from typing import Any

from infra_executors.constants import (
    AwsCredentials,
    GeneralConfiguration,
)
from infra_executors.constructors import build_environment_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)


logger = get_logger("network")


def create_network(creds: AwsCredentials, params: GeneralConfiguration,) -> Any:
    """Create vpc with private and subnet network, with internet access."""
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="network",
            action="create",
            config_dir="network",
            state_key=build_environment_state_key(params, "network"),
            variables_file_name="network.tfvars",
        ),
    )
    network_details = executor.get_outputs()
    if network_details:
        logger.info(
            "Network already exists. project_name=%s env_name=%s",
            params.project_name,
            params.env_name,
        )
        return network_details
    return executor.execute_apply()


def get_network_details(creds: AwsCredentials, params: GeneralConfiguration,) -> Any:
    """Get network details."""
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="network",
            action="outputs",
            config_dir="network",
            state_key=build_environment_state_key(params, "network"),
            variables_file_name="network.tfvars",
        ),
    )
    return executor.get_outputs()


def destroy_network(creds: AwsCredentials, params: GeneralConfiguration,) -> None:
    """Destroy vpc that was created with create_network from above."""
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="network",
            action="destroy",
            config_dir="network",
            state_key=build_environment_state_key(params, "network"),
            variables_file_name="network.tfvars",
        ),
    )
    return executor.execute_destroy()
