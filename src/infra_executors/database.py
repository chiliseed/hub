"""Creates the database inside a vpc."""
from typing import Any, NamedTuple

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_project_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)

logger = get_logger("db")


class DBConfigs(NamedTuple):
    """Configures db executor."""

    identifier: str
    name: str
    username: str
    password: str

    instance_type: str = "db.t2.large"
    allocated_storage: int = 100


def create_postgresql(
    creds: AwsCredentials, params: GeneralConfiguration, db_conf: DBConfigs
) -> Any:
    """Create a database."""
    logger.info("Executing run id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=db_conf,
        executor_configs=ExecutorConfiguration(
            name="postgres",
            action="create",
            config_dir="postgres",
            state_key=build_project_state_key(params, "postgres"),
        ),
    )
    return executor.execute_apply()


def destroy_postgresql(
    creds: AwsCredentials, params: GeneralConfiguration, db_conf: DBConfigs
) -> None:
    """Destroy database."""
    logger.info("Executing destroy postgres. run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=db_conf,
        executor_configs=ExecutorConfiguration(
            name="postgres",
            action="destroy",
            config_dir="postgres",
            state_key=build_project_state_key(params, "postgres"),
        ),
    )
    executor.execute_destroy()
    logger.info("DB destroyed")
