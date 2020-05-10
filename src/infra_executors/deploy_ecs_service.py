"""Deploys and removes demo application."""
import logging
from dataclasses import dataclass
from time import sleep
from typing import Any, Optional, List

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
class SecretEnvVar:
    name: str
    value_from: str


@dataclass
class DeploymentConf:
    container_port: int
    ecs_cluster: str
    ecs_executor_role_arn: str
    repo_url: str
    secrets: Optional[List[SecretEnvVar]]
    service_name: str
    target_group_arn: str
    version: str


def put_task_definition(
    creds: AwsCredentials, params: GeneralConfiguration, deploy_conf: DeploymentConf
) -> Any:
    """Pushes task definition for the specified service."""
    logger.info("Put ECS task definition for: %s", DEMO_APP)

    client = get_boto3_client("ecs", creds)
    if deploy_conf.secrets:
        secrets = [
            dict(name=s.name, valueFrom=s.value_from) for s in deploy_conf.secrets
        ]
    else:
        secrets = []

    task_definition = client.register_task_definition(
        family=deploy_conf.service_name,
        executionRoleArn=deploy_conf.ecs_executor_role_arn,
        cpu="128",
        memory="150",
        containerDefinitions=[
            {
                "name": deploy_conf.service_name,
                "image": f"{deploy_conf.repo_url}:{deploy_conf.version}",
                "portMappings": [
                    {"containerPort": deploy_conf.container_port, "protocol": "tcp"}
                ],
                "secrets": secrets,
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
    timeout_seconds: int = 1800,
    task_definition_arn: str = None,
) -> None:
    """Wait for service scale."""
    logger.info(
        "wait_for_service_scale cluster=%s service_name=%s desired_count=%s timeout_seconds=%s task_definition_arn=%s",
        cluster, service_name, desired_count, timeout_seconds, task_definition_arn
    )

    client = get_boto3_client("ecs", creds)
    waited_seconds = 0
    while waited_seconds <= timeout_seconds:
        logger.info("Checking if service scaled to %s waited_seconds=%s", desired_count, waited_seconds)
        resp = client.describe_services(cluster=cluster, services=[service_name])
        if not resp["services"]:
            logger.error("Service not found")
            return

        service = resp["services"][0]
        if task_definition_arn:
            logger.info(
                "Selecting service with task definition arn: %s", task_definition_arn
            )
            service = [
                d
                for d in service["deployments"]
                if d["taskDefinition"] == task_definition_arn
            ][0]

        logger.info("Scaling checking scale for service: %s", service)

        if int(service["runningCount"]) == desired_count:
            logger.info(
                "Services %s scaled to desired count of %d",
                service_name,
                desired_count,
            )
            return

        sleep(1)
        waited_seconds += 1

    raise Exception(
        f"Service {service_name} scale to "
        f"desired count of {desired_count} TIMED OUT"
    )


def launch_task_in_cluster(
    creds: AwsCredentials, deploy_conf: DeploymentConf, task_definition: Any,
) -> Any:
    """Launch service in cluster."""
    logger.info(
        "Creating service for task definition: %s",
        task_definition["taskDefinition"]["taskDefinitionArn"],
    )
    client = get_boto3_client("ecs", creds)
    try:
        logger.info("Checking existing services")
        resp = client.describe_services(
            cluster=deploy_conf.ecs_cluster, services=[deploy_conf.service_name]
        )
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


def deploy_ecs_service(
    creds: AwsCredentials, params: GeneralConfiguration, deploy_conf: DeploymentConf
) -> None:
    """Deploys latest demo application."""
    logger.info(
        "Creating task definition service %s to cluster: %s",
        deploy_conf.service_name,
        deploy_conf.ecs_cluster,
    )
    task_definition = put_task_definition(creds, params, deploy_conf)
    launch_task_in_cluster(creds, deploy_conf, task_definition)
    wait_for_service_scale(
        creds,
        deploy_conf.ecs_cluster,
        deploy_conf.service_name,
        1,
        task_definition_arn=task_definition["taskDefinition"]["taskDefinitionArn"],
    )
    logger.info("Service %s deployed", deploy_conf.service_name)


def remove_ecs_service(creds: AwsCredentials, deploy_conf: DeploymentConf) -> None:
    """Remove ecs service from cluster."""
    logger.info(
        "Removing %s from cluster %s", deploy_conf.service_name, deploy_conf.ecs_cluster
    )
    client = get_boto3_client("ecs", creds)

    logger.info("Get task definitions: %s", deploy_conf.service_name)
    task_definitions = client.list_task_definitions(
        familyPrefix=deploy_conf.service_name, sort="DESC",
    )
    if not task_definitions["taskDefinitionArns"]:
        logger.info("Found 0 task definitions for family %s", deploy_conf.service_name)
    else:
        logger.info("Scaling down %s", SERVICE_NAME)
        client.update_service(
            cluster=deploy_conf.ecs_cluster,
            service=deploy_conf.service_name,
            taskDefinition=task_definitions["taskDefinitionArns"][0],
            desiredCount=0,
            deploymentConfiguration={
                "maximumPercent": 200,
                "minimumHealthyPercent": 100,
            },
            forceNewDeployment=True,
        )
        wait_for_service_scale(
            creds, deploy_conf.ecs_cluster, deploy_conf.service_name, 0
        )

    logger.info("Deleting service %s", deploy_conf.service_name)
    client.delete_service(
        cluster=deploy_conf.ecs_cluster, service=deploy_conf.service_name, force=True
    )

    logger.info("Removing task definitions")
    for task_definition in task_definitions["taskDefinitionArns"]:
        client.deregister_task_definition(taskDefinition=task_definition)
        logger.info("Deregisted %s", task_definition)

    logger.info("Service removed")
