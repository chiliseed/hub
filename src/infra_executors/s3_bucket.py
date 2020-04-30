"""Manages AWS S3 buckets."""
import logging
from typing import Any, List, NamedTuple

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_resource_state_key
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)

logger = logging.getLogger(__name__)


class S3Configs(NamedTuple):
    """Bucket configuration."""
    bucket_name: str
    acl: str


def create_bucket(
    creds: AwsCredentials, params: GeneralConfiguration, s3_conf: S3Configs
) -> Any:
    """Create a bucket."""
    logger.info("Executing run id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=s3_conf,
        executor_configs=ExecutorConfiguration(
            name="s3_bucket",
            action="create",
            config_dir="s3_bucket",
            state_key=build_resource_state_key(params, "s3_bucket"),
        ),
    )
    return executor.execute_apply()


def destroy_bucket(
    creds: AwsCredentials, params: GeneralConfiguration, s3_conf: S3Configs
) -> None:
    """Destroy a bucket."""
    logger.info("Executing destroy postgres. run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=s3_conf,
        executor_configs=ExecutorConfiguration(
            name="s3_bucket",
            action="destroy",
            config_dir="s3_bucket",
            state_key=build_resource_state_key(params, "s3_bucket"),
        ),
    )
    executor.execute_destroy()
    logger.info("Bucket removed")
