import argparse
import os
from typing import NamedTuple

import boto3

from infra_executors.constants import AwsCredentials, KEYS_DIR, GeneralConfiguration
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import TerraformExecutor, ExecutorConfiguration

logger = get_logger("ecs-infra-executor")


class ECSConfigs(NamedTuple):
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


def get_session(region: str) -> boto3.session.Session:
    """Return new thread-safe Session object.

    Each boto3 client/resource should use it to interact with AWS services.

    More info about it:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html#multithreading-multiprocessing

    Parameters
    ----------
    region : str
        name of the aws region. Example: us-east-1

    Returns
    -------
    boto3.session.Session
        boto3.session.Session instance
    """
    session_config = {"region_name": region}

    return boto3.session.Session(**session_config)


def get_boto3_client(service_name: str, aws_creds: AwsCredentials):
    """Initialize boto3 for the service.

    Parameters
    ----------
    aws_creds: AwsCredentials
        aws credentials
    service_name: str
        name of the service. Example: ssm, ec2, s3

    Returns
    -------
    boto3.client
    """
    session = get_session(aws_creds.region)
    return session.client(
        service_name,
        aws_access_key_id=aws_creds.access_key,
        aws_secret_access_key=aws_creds.secret_key,
    )


def get_ecs_ami_id(aws_creds: AwsCredentials):
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
    ssm_client = get_boto3_client('ssm', aws_creds)
    param = ssm_client.get_parameter(
        Name="/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id",
    )
    return param['Parameter']['Value']


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
    ec2_client = get_boto3_client('ec2', aws_creds)
    key_pair = ec2_client.create_key_pair(KeyName=name)

    with open(os.path.join(KEYS_DIR, f"{key_pair['KeyName']}_fingerprint.txt"), 'w') as fingerprint_file:
        fingerprint_file.write(key_pair['KeyFingerprint'])

    key_pair_path = os.path.join(KEYS_DIR, f"{key_pair['KeyName']}.pem")
    with open(key_pair_path, 'w') as key_file:
        key_file.write(key_pair['KeyMaterial'])

    return key_pair_path


def create_ecs_cluster(creds: AwsCredentials, params: GeneralConfiguration, ecs_conf: ECSConfigs):
    """Create ecs cluster with asg."""
    logger.info("Executing run_id=%s", params.run_id)
    if not ecs_conf.ssh_key_name:
        logger.info("Creating new ssh key-pair. run_id=%s", params.run_id)
        ecs_conf = ecs_conf._replace(
            ssh_key_name=create_ssh_key(
                f"{params.project_name}_{params.env_name}", creds
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
            state_key=build_state_key(params, 'ecs'),
            variables_file_name=""
        )
    )
    return executor.execute_apply()


def destroy_ecs(creds: AwsCredentials, params: GeneralConfiguration, ecs_conf: ECSConfigs):
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
            state_key=build_state_key(params, 'ecs'),
            variables_file_name=""
        )
    )
    return executor.execute_destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create/destroy db in the provides vpc."
    )
    parser.add_argument(
        "cmd",
        type=str,
        default="create",
        help="Sub command. One of: create/destroy",
    )
    parser.add_argument(
        "project_name",
        type=str,
        help="The name of your project. Example: chiliseed",
    )
    parser.add_argument(
        "environment",
        type=str,
        default="develop",
        help="The name of your environment. Example: develop",
    )
    parser.add_argument(
        "vpc_id",
        type=str,
        help="The id of the vpc. Example: vpc-0c5b94e64b709fa24",
    )
    parser.add_argument("--aws-access-key", type=str, dest="aws_access_key")
    parser.add_argument("--aws-secret-key", type=str, dest="aws_secret_key")
    parser.add_argument(
        "--aws-region", type=str, default="us-east-2", dest="aws_region"
    )
    parser.add_argument(
        "--run-id", type=str, default=1, dest="run_id"
    )

    args = parser.parse_args()

    aws_creds = AwsCredentials(
        args.aws_access_key, args.aws_secret_key, "", args.aws_region
    )
    common = GeneralConfiguration(
        args.project_name, args.environment, args.run_id, args.vpc_id
    )
    cmd_configs = ECSConfigs(
        cluster="demo",
        instance_group_name="demo",
        cloudwatch_prefix="demo",
        ssh_key_name="demo_dev",
        ecs_aws_ami="ami-0fbd313043845c4f2",
    )

    if args.cmd == "create":
        create_ecs_cluster(aws_creds, common, cmd_configs)
    if args.cmd == "destroy":
        destroy_ecs(aws_creds, common, cmd_configs)
