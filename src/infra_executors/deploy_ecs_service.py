"""Deploys and removes demo application."""
import argparse
import logging
from dataclasses import dataclass
from time import sleep
from typing import Any

import botocore.exceptions  # type: ignore

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.utils import get_boto3_client


logger = logging.getLogger(__name__)

DEMO_APP = "demo-api"
DEMO_API_IMAGE_URI = "chiliseed/demo-api:latest"
CONTAINER_PORT = 7878
ALB_PORT = 80
CONTAINER_HEALTH_CHECK_URI = "/health/check"
SERVICE_NAME = FAMILY_NAME = f"chiliseed-{DEMO_APP}"


class DeployError(Exception):
    """Exceptions thrown by put task definition."""


@dataclass
class DeploymentConf:
    ecs_cluster: str
    ecs_executor_role_arn: str
    service_name: str
    repo_url: str
    version: str
    container_port: int
    target_group_arn: str


def put_task_definition(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    deploy_conf: DeploymentConf
) -> Any:
    """Pushes task definition for the specified service."""
    logger.info("Put ECS task definition for: %s", DEMO_APP)

    client = get_boto3_client("ecs", creds)
    task_definition = client.register_task_definition(
        family=deploy_conf.service_name,
        executionRoleArn=deploy_conf.ecs_executor_role_arn,
        cpu="128",
        memory="100",
        containerDefinitions=[
            {
                "name": deploy_conf.service_name,
                "image": f"{deploy_conf.repo_url}:{deploy_conf.version}",
                "portMappings": [{"containerPort": deploy_conf.container_port, "protocol": "tcp"}],
                "essential": True,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"{params.env_name}/{params.project_name}",
                        "awslogs-create-group": "true",
                        "awslogs-region": creds.region,
                        "awslogs-stream-prefix": f"{deploy_conf.service_name}",
                    },
                },
            }
        ],
        tags=[
            {"key": "Environment", "value": params.env_name},
            {"key": "Project", "value": "demo-api"},
        ],
    )

    logger.info(
        "Success putting ECS task definition: %s",
        task_definition["taskDefinition"]["taskDefinitionArn"],
    )
    return task_definition


def wait_for_service_scale(
    creds: AwsCredentials,
    cluster: str,
    service_name: str,
    desired_count: int,
    timeout_seconds: int = 10,
) -> None:
    """Wait for service scale."""
    client = get_boto3_client("ecs", creds)
    waited_seconds = 0
    while waited_seconds < timeout_seconds:
        logger.info("Checking if service scaled to %s", desired_count)
        resp = client.describe_services(cluster=cluster, services=[service_name])

        if not resp["services"]:
            raise Exception("Service not found")
        if resp["service"][0]["runningCount"] == desired_count:
            logger.info(
                "Services %s scaled to desired count of %d",
                service_name,
                desired_count,
            )
            return

        waited_seconds += 1
        sleep(1)

    raise Exception(
        f"Service {service_name} scale to "
        f"desired count of {desired_count} TIMED OUT"
    )


def launch_task_in_cluster(
    creds: AwsCredentials, deploy_conf: DeploymentConf, task_definition: Any,
) -> Any:
    """Launch service in cluster."""
    logger.info("Creating service for task definition: %s", task_definition["taskDefinition"]["taskDefinitionArn"])
    client = get_boto3_client("ecs", creds)
    try:
        logger.info("Checking existing services")
        resp = client.describe_services(cluster=deploy_conf.ecs_cluster, services=[deploy_conf.service_name])
        if resp["services"]:
            logger.info("Updating existing %s service", deploy_conf.service_name)
            client.update_service(
                cluster=deploy_conf.ecs_cluster,
                service=deploy_conf.service_name,
                taskDefinition=task_definition["taskDefinition"]["taskDefinitionArn"],
                desiredCount=1,
                deploymentConfiguration={
                    "maximumPercent": 200,
                    "minimumHealthyPercent": 100,
                },
                forceNewDeployment=True,
            )
            return
    except botocore.exceptions.ClientError:
        pass

    logger.info("Deploying new %s service", deploy_conf.service_name)
    response = client.create_service(
        cluster=deploy_conf.ecs_cluster,
        serviceName=deploy_conf.service_name,
        taskDefinition=task_definition["taskDefinition"]["taskDefinitionArn"],
        desiredCount=1,
        launchType="EC2",
        schedulingStrategy="REPLICA",
        deploymentController={"type": "ECS"},  # rolling update
        deploymentConfiguration={"maximumPercent": 200, "minimumHealthyPercent": 100},
        loadBalancers=[
            {
                "targetGroupArn": deploy_conf.target_group_arn,
                "containerName": deploy_conf.service_name,
                "containerPort": deploy_conf.container_port,
            }
        ],
    )
    logger.debug("ECS create service response: %s", response)


def deploy(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    deploy_conf: DeploymentConf
) -> None:
    """Deploys latest demo application."""
    logger.info("Creating task definition service %s to cluster: %s", deploy_conf.service_name, deploy_conf.ecs_cluster)
    task_definition = put_task_definition(creds, params, deploy_conf)
    launch_task_in_cluster(creds, deploy_conf, task_definition)
    logger.info("Service %s deployed", deploy_conf.service_name)


def remove(
    creds: AwsCredentials, params: GeneralConfiguration, cluster_name: str
) -> None:
    """Remove demo application from cluster."""
    cluster = f"{cluster_name}-{params.env_name}"
    logger.info("Removing %s from cluster %s", DEMO_APP, cluster_name)
    client = get_boto3_client("ecs", creds)

    logger.info("Get task definitions: %s", FAMILY_NAME)
    task_definitions = client.list_task_definitions(
        familyPrefix=FAMILY_NAME, sort="DESC",
    )
    if not task_definitions["taskDefinitionArns"]:
        logger.info("Found 0 task definitions for family %s", FAMILY_NAME)
    else:
        logger.info("Scaling down %s", SERVICE_NAME)
        client.update_service(
            cluster=cluster,
            service=SERVICE_NAME,
            taskDefinition=task_definitions["taskDefinitionArns"][0],
            desiredCount=0,
            deploymentConfiguration={
                "maximumPercent": 200,
                "minimumHealthyPercent": 100,
            },
            forceNewDeployment=True,
        )
        wait_for_service_scale(creds, cluster, SERVICE_NAME, 0)

    logger.info("Deleting service %s", SERVICE_NAME)
    client.delete_service(cluster=cluster, service=SERVICE_NAME, force=True)

    logger.info("Removing task definitions")
    for task_definition in task_definitions["taskDefinitionArns"]:
        client.deregister_task_definition(taskDefinition=task_definition)
        logger.info("Deregisted %s", task_definition)

    logger.info("Demo api removed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="deploy/remove demo api in provided ecs cluster/vpc."
    )
    parser.add_argument(
        "cmd", type=str, default="deploy", help="Sub command. One of: deploy/remove",
    )
    parser.add_argument(
        "project_name", type=str, help="The name of your project. Example: chiliseed",
    )
    parser.add_argument(
        "environment",
        type=str,
        default="develop",
        help="The name of your environment. Example: develop",
    )
    parser.add_argument(
        "vpc_id", type=str, help="The id of the vpc. Example: vpc-0c5b94e64b709fa24",
    )
    parser.add_argument(
        "cluster", type=str, help="Name of ECS cluster to deploy to",
    )
    parser.add_argument(
        "target_group",
        type=str,
        help="Load balancer target group arn via which the service will " "be served",
    )
    parser.add_argument("--aws-access-key", type=str, dest="aws_access_key")
    parser.add_argument("--aws-secret-key", type=str, dest="aws_secret_key")
    parser.add_argument(
        "--aws-region", type=str, default="us-east-2", dest="aws_region"
    )
    parser.add_argument("--run-id", type=str, default=1, dest="run_id")

    args = parser.parse_args()

    aws_creds = AwsCredentials(
        args.aws_access_key, args.aws_secret_key, "", args.aws_region
    )
    common = GeneralConfiguration(
        args.project_name, args.environment, args.run_id, args.vpc_id
    )

    if args.cmd == "deploy":
        deploy(aws_creds, common, args.cluster, args.target_group)
    if args.cmd == "remove":
        remove(aws_creds, common, args.cluster)
