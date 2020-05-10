import logging
from typing import NamedTuple

from infra_executors.constants import GeneralConfiguration, AwsCredentials
from infra_executors.constructors import build_service_state_key
from infra_executors.terraform_executor import TerraformExecutor, ExecutorConfiguration

logger = logging.getLogger(__name__)


class BuildWorkerConfigs(NamedTuple):
    ssh_key_name: str
    aws_access_key_id: str
    aws_access_key_secret: str
    env_name: str
    code_version: str
    service_name: str
    ecr_url: str
    valid_until: str
    dockerfile: str
    dockerfile_target: str = ""
    worker_ami: str = "ami-0cef0a0c24a179fb3"
    spot_max_price: str = "0.1"


def launch_build_worker_server(
    creds: AwsCredentials, params: GeneralConfiguration, run_config: BuildWorkerConfigs
):
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="build_worker",
            action="create",
            config_dir="build_worker",
            state_key=build_service_state_key(params, "build_worker"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def remove_build_worker_server(
    creds: AwsCredentials, params: GeneralConfiguration, run_config: BuildWorkerConfigs
):
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=run_config,
        executor_configs=ExecutorConfiguration(
            name="build_worker",
            action="destroy",
            config_dir="build_worker",
            state_key=build_service_state_key(params, "build_worker"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()
