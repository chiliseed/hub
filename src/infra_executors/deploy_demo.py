import argparse
from typing import Dict

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import TerraformExecutor, ExecutorConfiguration
from infra_executors.utils import get_boto3_client


logger = get_logger("deploy-demo")

DEMO_APP = 'demo-api'
DEMO_API_IMAGE_URI = "chiliseed/demo-api:latest"
CONTAINER_PORT = 7878
ALB_PORT = 80
CONTAINER_HEALTH_CHECK_URI = "/health/check"


class DeployError(Exception):
    """Exceptions thrown by put task definition."""


def put_task_definition(creds: AwsCredentials, params: GeneralConfiguration) -> Dict:
    """Pushes task definition for Chiliseed demo api."""
    logger.info("Getting cluster details. project=%s env=%s", params.project_name, params.env_name)
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="ecs",
            action="output",
            config_dir="ecs",
            state_key=build_state_key(params, 'ecs'),
            variables_file_name=""
        )
    )
    outputs = executor.get_outputs()
    if not outputs:
        raise DeployError("Failed to get ecs outputs")

    logger.info("Put ECS task definition for: %s", DEMO_APP)

    client = get_boto3_client("ecs", creds)
    task_definition = client.register_task_definition(
        family=f"chiliseed-{DEMO_APP}",
        executionRoleArn=outputs['ecs_executor_role_arn'],
        cpu='100',
        memory='128m',
        containerDefinitions=[{
            "name": DEMO_APP,
            "image": DEMO_API_IMAGE_URI,
            "portMappings": [{
                'containerPort': 7878,
                'hostPort': 0,  # host port will be assigned dynamically
                'protocol': 'tcp'
            }],
            "essential": True,
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "chiliseed-demo-api",
                    "awslogs-region": creds.region,
                    "awslogs-stream-prefix": "demo-api",
                }
            }
        }],
        tags=[
            {"key": "Environment", "value": params.env_name},
            {"key": "Project", "value": "demo-api"},
        ]
    )

    logger.info("Success putting ECS task definition: %s", task_definition['task_definition']['taskDefinitionArn'])
    return task_definition


def create_target_group(creds: AwsCredentials, name: str, container_port: int, vpc_id: str, health_check_uri: str) -> Dict:
    """Create target group to route traffic to container."""
    client = get_boto3_client("ecs", creds)
    resp = client.describe_target_groups(Names=[name])
    if resp['TargetGroups']:
        logger.info("Found existing target group: %s", name)
        return resp['TargetGroups'][0]

    logger.info("Creating target group for: %s", name)

    return client.create_target_group(
        Name=name,
        Protocol='HTTP',
        Port=container_port,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='traffic-port',
        HealthCheckPath=health_check_uri,
        HealthCheckIntervalSeconds=30,
        HealthCheckTimeoutSeconds=5,
        HealthyThresholdCount=5,
        UnhealthyThresholdCount=2,
        Matcher={
            "HttpCode": 200,
            "TargetType": "instance",
        }
    )


def create_listener_for_target_group(creds: AwsCredentials, alb_port: int, alb_arn: str, target_group_arn: str) -> Dict:
    """Create listener that forwards traffic to target group."""
    logger.info("Creating listener on alb %s for target group %s", alb_arn, target_group_arn)
    client = get_boto3_client("ecs", creds)
    return client.create_listener(
        LoadBalancerArn=alb_arn,
        Protocol='HTTP',
        Port=alb_port,
        DefaultActions=[{
            "Type": "forward",
            "TargetGroupArn": target_group_arn,
        }]
    )


def launch_task_in_cluster(creds: AwsCredentials, params: GeneralConfiguration, task_definition: Dict, cluster: str):
    """Launch service in cluster."""
    target_group = create_target_group(
        creds,
        "demo-api",
        container_port=CONTAINER_PORT,
        vpc_id=params.vpc_id,
        health_check_uri=CONTAINER_HEALTH_CHECK_URI
    )
    # get alb
    executor = TerraformExecutor(
        creds=creds,
        general_configs=params,
        cmd_configs=None,
        executor_configs=ExecutorConfiguration(
            name="alb",
            action="output",
            config_dir="alb",
            state_key=build_state_key(params, 'alb'),
            variables_file_name=""
        )
    )
    outputs = executor.get_outputs()
    if not outputs:
        raise DeployError("Failed to get ecs outputs")

    create_listener_for_target_group(
        creds, ALB_PORT, outputs['alb_arn'], target_group['TargetGroupArn']
    )

    client = get_boto3_client("ecs", creds)
    client.create_service(
        cluster=cluster,
        serviceName="chiliseed-demo-api",
        taskDefinition=task_definition['task_definition']['taskDefinitionArn'],
        desiredCount=1,
        launchType='EC2',
        schedulingStrategy="REPLICA",
        deploymentController={
            "type": "ECS"  # rolling update
        },
        deploymentConfiguration={
            "maximumPercent": 200,
            "minimumHealthyPercent": 100,
        },
        loadBalancers={
            "targetGroupArn": target_group['TargetGroupArn']
        }
    )


def deploy(creds: AwsCredentials, params: GeneralConfiguration, cluster: str):
    logger.info("Deploying demo api to cluster: %s", cluster)
    task_definition = put_task_definition(creds, params)
    launch_task_in_cluster(creds, params, task_definition, cluster)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="deploy/remove demo api in provided ecs cluster/vpc."
    )
    parser.add_argument(
        "cmd",
        type=str,
        default="deploy",
        help="Sub command. One of: deploy/remove",
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
    parser.add_argument(
        "cluster",
        type=str,
        help="Name of ECS cluster to deploy to",
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

    if args.cmd == "deploy":
        deploy(aws_creds, common, args.cluster)
    if args.cmd == "destroy":
        destroy_ecs(aws_creds, common, cmd_configs)
