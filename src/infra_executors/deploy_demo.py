"""Deploys and removes demo application."""
import argparse
from time import sleep
from typing import Any

import botocore.exceptions  # type: ignore

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.logger import get_logger
from infra_executors.utils import get_boto3_client


logger = get_logger("deploy-demo")

DEMO_APP = "demo-api"
DEMO_API_IMAGE_URI = "chiliseed/demo-api:latest"
CONTAINER_PORT = 7878
ALB_PORT = 80
CONTAINER_HEALTH_CHECK_URI = "/health/check"
SERVICE_NAME = FAMILY_NAME = f"chiliseed-{DEMO_APP}"


class DeployError(Exception):
    """Exceptions thrown by put task definition."""


def put_task_definition(
    creds: AwsCredentials, params: GeneralConfiguration, cluster: str
) -> Any:
    """Pushes task definition for Chiliseed demo api."""
    logger.info(
        "Getting ecs executor role. project=%s env=%s",
        params.project_name,
        params.env_name,
    )
    iam_client = get_boto3_client("iam", creds)
    ecs_executor = iam_client.get_role(
        RoleName=f"{params.env_name}_{cluster}_ecs_task_executor"
    )
    logger.info("Put ECS task definition for: %s", DEMO_APP)

    client = get_boto3_client("ecs", creds)
    task_definition = client.register_task_definition(
        family=FAMILY_NAME,
        executionRoleArn=ecs_executor["Role"]["Arn"],
        cpu="128",
        memory="100",
        containerDefinitions=[
            {
                "name": DEMO_APP,
                "image": DEMO_API_IMAGE_URI,
                "portMappings": [{"containerPort": CONTAINER_PORT, "protocol": "tcp"}],
                "essential": True,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "chiliseed-demo-api",
                        "awslogs-create-group": "true",
                        "awslogs-region": creds.region,
                        "awslogs-stream-prefix": "demo-api",
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


def create_target_group(
    creds: AwsCredentials,
    name: str,
    container_port: int,
    vpc_id: str,
    health_check_uri: str,
) -> Any:
    """Create target group to route traffic to container."""
    client = get_boto3_client("elbv2", creds)
    try:
        resp = client.describe_target_groups(Names=[name])
        return resp["TargetGroups"][0]
    except botocore.exceptions.ClientError:
        logger.info("Target group not found")

    logger.info("Creating target group for: %s", name)

    return client.create_target_group(
        Name=name,
        Protocol="HTTP",
        Port=container_port,
        VpcId=vpc_id,
        HealthCheckProtocol="HTTP",
        HealthCheckPort="traffic-port",
        HealthCheckPath=health_check_uri,
        HealthCheckIntervalSeconds=30,
        HealthCheckTimeoutSeconds=5,
        HealthyThresholdCount=5,
        UnhealthyThresholdCount=2,
        Matcher={"HttpCode": "200"},
        TargetType="instance",
    )["TargetGroups"][0]


def create_listener_for_target_group(
    creds: AwsCredentials, alb_arn: str, target_group_arn: str, acm_arn: str
) -> Any:
    """Create listener that forwards traffic to target group."""
    client = get_boto3_client("elbv2", creds)
    https = None
    http = None
    try:
        logger.info("Checking for existing listeners")
        resp = client.describe_listeners(LoadBalancerArn=alb_arn)
        for listener in resp["Listeners"]:
            actions = next(
                filter(
                    lambda o: o["TargetGroupArn"] == target_group_arn,
                    listener["DefaultActions"],
                ),
                None,
            )

            if actions:
                if listener["Protocol"] == "HTTP":
                    logger.info("Found listener for http")
                    http = listener
                elif listener["Protocol"] == "HTTPS":
                    logger.info("Found listener for https")
                    https = listener
                else:
                    logger.warning("None http listener found: %s", listener["Protocol"])
    except botocore.exceptions.ClientError:
        logger.info("Listener not found")

    if not http:
        logger.info(
            "Creating http listener on alb %s for target group %s",
            alb_arn,
            target_group_arn,
        )
        client.create_listener(
            LoadBalancerArn=alb_arn,
            Protocol="HTTP",
            Port="80",
            DefaultActions=[
                {
                    "Type": "redirect",
                    "RedirectConfig": {
                        "Protocol": "HTTPS",
                        "Port": "#{port}",
                        "Host": "#{host}",
                        "Path": "/#{path}",
                        "Query": "#{query}",
                        "StatusCode": "HTTP_301",
                    },
                }
            ],
        )
    if not https:
        logger.info(
            "Creating https listener on alb %s for target group %s",
            alb_arn,
            target_group_arn,
        )
        https = client.create_listener(
            LoadBalancerArn=alb_arn,
            Protocol="HTTPS",
            Port=443,
            Certificates=[{"CertificateArn": acm_arn}],
            DefaultActions=[{"Type": "forward", "TargetGroupArn": target_group_arn}],
        )

    return https


def launch_task_in_cluster(
    creds: AwsCredentials, target_group_arn: str, task_definition: Any, cluster: str,
) -> Any:
    """Launch service in cluster."""
    client = get_boto3_client("ecs", creds)
    try:
        resp = client.describe_services(cluster=cluster, services=[SERVICE_NAME])
        if resp["services"]:
            logger.info("Updating existing %s service", SERVICE_NAME)
            client.update_service(
                cluster=cluster,
                service=SERVICE_NAME,
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
        logger.info("Deploying new %s service", SERVICE_NAME)

    client.create_service(
        cluster=cluster,
        serviceName=SERVICE_NAME,
        taskDefinition=task_definition["taskDefinition"]["taskDefinitionArn"],
        desiredCount=1,
        launchType="EC2",
        schedulingStrategy="REPLICA",
        deploymentController={"type": "ECS"},  # rolling update
        deploymentConfiguration={"maximumPercent": 200, "minimumHealthyPercent": 100,},
        loadBalancers=[
            {
                "targetGroupArn": target_group_arn,
                "containerName": DEMO_APP,
                "containerPort": CONTAINER_PORT,
            }
        ],
    )


def deploy(
    creds: AwsCredentials,
    params: GeneralConfiguration,
    cluster: str,
    target_group_arn: str,
) -> None:
    """Deploys latest demo application."""
    logger.info("Deploying demo api to cluster: %s", cluster)
    task_definition = put_task_definition(creds, params, cluster)
    launch_task_in_cluster(
        creds, target_group_arn, task_definition, f"{cluster}-{params.env_name}",
    )
    logger.info("Demo api deployed")


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
