"""Manages ecs cluster."""
import os
from typing import Any, NamedTuple

from infra_executors.constants import (
    AwsCredentials,
    GeneralConfiguration,
    KEYS_DIR,
)
from infra_executors.constructors import build_project_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import (
    ExecutorConfiguration,
    TerraformExecutor,
)
from infra_executors.utils import get_boto3_client

logger = get_logger("ecs")


class ECSConfigs(NamedTuple):
    """Configures ecs cluster."""

    cluster: str
    instance_group_name: str
    cloudwatch_prefix: str

    # ami id will be retrieved from aws ssm if not provided
    ecs_aws_ami: str = ""
    # the key will be created automatically, if not provided
    ssh_key_name: str = ""
    instance_type: str = "t2.micro"
    max_size: int = 1
    min_size: int = 1
    desired_capacity: int = 1
    alb_security_group_id: str = ""


def get_ecs_ami_id(aws_creds: AwsCredentials) -> str:
    """Retrieve the id of the official aws ecs optimized image for the region.

    Parameters
    ----------
    aws_creds: AwsCredentials
        aws credentials

    Returns
    -------
    str:
        aws ecs optimized ami id
    """
    ssm_client = get_boto3_client("ssm", aws_creds)
    param = ssm_client.get_parameter(
        Name="/aws/service/ecs/optimized-ami/" "amazon-linux-2/recommended/image_id",
    )
    return str(param["Parameter"]["Value"])


def create_ssh_key(name: str, aws_creds: AwsCredentials) -> str:
    """Create new ssh key and return it's pem file.

    Parameters
    ----------
    name : str
        created key will have this name
    aws_creds : AwsCredentials
        aws credentials to create a connection via boto

    Returns
    -------
    str
        local path to pem key
    """
    pem_key_path = os.path.join(KEYS_DIR, f"{name}.pem")
    if os.path.exists(pem_key_path):
        logger.info("Pem key %s is in our system", name)
        return name

    ec2_client = get_boto3_client("ec2", aws_creds)
    key_pair = ec2_client.create_key_pair(KeyName=name)

    with open(
        os.path.join(KEYS_DIR, f"{key_pair['KeyName']}_fingerprint.txt"), "w"
    ) as fingerprint_file:
        fingerprint_file.write(key_pair["KeyFingerprint"])

    key_pair_path = os.path.join(KEYS_DIR, f"{key_pair['KeyName']}.pem")
    with open(key_pair_path, "w") as key_file:
        key_file.write(key_pair["KeyMaterial"])

    return name


def create_ecs_cluster(
    creds: AwsCredentials, params: GeneralConfiguration, ecs_conf: ECSConfigs
) -> Any:
    """Create ecs cluster with asg."""
    logger.info("Executing run_id=%s", params.run_id)
    if not ecs_conf.ssh_key_name:
        logger.info("Creating new ssh key-pair. run_id=%s", params.run_id)
        ecs_conf = ecs_conf._replace(
            ssh_key_name=create_ssh_key(
                f"{params.project_name}_{params.env_name}_{params.env_slug}", creds
            )
        )
    if not ecs_conf.ecs_aws_ami:
        logger.info("Retrieving aws ami id. run_id=%s", params.run_id)
        ecs_conf = ecs_conf._replace(ecs_aws_ami=get_ecs_ami_id(creds))

    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=ecs_conf,
        executor_configs=ExecutorConfiguration(
            name="ecs",
            action="create",
            config_dir="ecs",
            state_key=build_project_state_key(params, "ecs"),
            variables_file_name="",
        ),
    )
    return executor.execute_apply()


def destroy_ecs_cluster(
    creds: AwsCredentials, params: GeneralConfiguration, ecs_conf: ECSConfigs
) -> Any:
    """Destroy ecs cluster and its resources."""
    logger.info("Executing run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=ecs_conf,
        executor_configs=ExecutorConfiguration(
            name="ecs",
            action="destroy",
            config_dir="ecs",
            state_key=build_project_state_key(params, "ecs"),
            variables_file_name="",
        ),
    )
    return executor.execute_destroy()
