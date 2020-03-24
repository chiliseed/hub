import logging
from typing import NamedTuple, List, Any

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_project_state_key
from infra_executors.terraform_executor import TerraformExecutor, ExecutorConfiguration

logger = logging.getLogger(__name__)


class CacheConfigs(NamedTuple):
    """Configures cache executor."""

    identifier: str
    name: str

    instance_type: str = "cache.t2.small"
    engine: str = "redis"
    number_of_nodes: int = 1
    parameter_group_name: str = "default.redis5.0"
    engine_version: str = "5.0.6"
    allowed_security_groups_ids: List[str] = []
    apply_immediately: bool = True
    snapshot_retention_limit_days: int = 0


def create_cache(
    creds: AwsCredentials, params: GeneralConfiguration, cache_conf: CacheConfigs
) -> Any:
    """Create a database."""
    logger.info("Executing run id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=cache_conf,
        executor_configs=ExecutorConfiguration(
            name="elasticache",
            action="create",
            config_dir="elasticache",
            state_key=build_project_state_key(params, "elasticache"),
        ),
    )
    return executor.execute_apply()


def destroy_cache(
    creds: AwsCredentials, params: GeneralConfiguration, cache_conf: CacheConfigs
) -> None:
    """Destroy cache."""
    logger.info("Executing destroy redis. run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=cache_conf,
        executor_configs=ExecutorConfiguration(
            name="elasticache",
            action="destroy",
            config_dir="elasticache",
            state_key=build_project_state_key(params, "elasticache"),
        ),
    )
    executor.execute_destroy()
    logger.info("Cache destroyed")


def get_cache_details(
    creds: AwsCredentials, params: GeneralConfiguration, cache_conf: CacheConfigs
) -> Any:
    """Get terraform outputs for elasticache resource."""
    logger.info("Executing destroy redis. run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=cache_conf,
        executor_configs=ExecutorConfiguration(
            name="elasticache",
            action="outputs",
            config_dir="elasticache",
            state_key=build_project_state_key(params, "elasticache"),
        ),
    )
    return executor.get_outputs()
