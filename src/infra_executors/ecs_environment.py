"""Manages environment global parts and project infra."""
from typing import NamedTuple, Any, Dict

from infra_executors.alb import create_alb, ALBConfigs, destroy_alb, get_alb_details
from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs import (
    ECSConfigs,
    create_ecs_cluster,
    destroy_ecs_cluster,
    get_ecs_cluster_details,
)
from infra_executors.logger import get_logger
from infra_executors.network import (
    create_network,
    get_network_details,
)
from infra_executors.route53 import (
    create_route53,
    Route53Configuration,
    destroy_route53,
)

logger = get_logger("ecs-env")


class ESCEnvironmentError(Exception):
    """Raised to indicate any errors in the process of building/destroying."""


class EnvConfigs(NamedTuple):
    """Configuration parameters required to create an environment."""

    domain: str
    route53: Route53Configuration


def create_global_parts(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    route53_conf: Route53Configuration,
):
    """Creates environment parts that are shared between multiple projects/services.

    Examples:
        same vpc can host multiple projects, so vpc with name 'development` can host
        demo api, demo micro service 2 and etc.
    """
    logger.info(
        "Creating environment network. run_id=%s project_name=%s environment=%s",
        common_conf.run_id,
        common_conf.project_name,
        common_conf.env_name,
    )
    network = create_network(creds, common_conf)
    logger.info("Created new vpc %s", network["vpc_id"])

    logger.info("Setting up route 53 for the project")
    route53 = create_route53(creds, common_conf, route53_conf)
    logger.info("Created new route53 zone: %s", route53["primary_zone_id"]["value"])
    return network, route53


def launch_project_infra(
    creds: AwsCredentials, common_conf: GeneralConfiguration
) -> Any:
    """Launch infrastructure for new service.

    common_conf.project_name here relates to service being launched.
    """
    if not common_conf.vpc_id:
        raise ESCEnvironmentError("Must provide VPC ID.")

    logger.info("Creating alb.")
    alb_conf = ALBConfigs(
        alb_name=f"{common_conf.project_name}-{common_conf.env_slug}",
        open_ports=[],
    )
    alb = create_alb(creds, common_conf, alb_conf)
    logger.info(
        "Created alb %s with dns %s", alb["alb_name"]["value"], alb["alb_arn"]["value"],
    )

    logger.info("Launching ECS cluster")
    ecs_conf = build_ecs_conf(alb["alb_security_group_id"]["value"], common_conf)
    ecs = create_ecs_cluster(creds, common_conf, ecs_conf)
    logger.info("Created ECS cluster %s", ecs["cluster"])
    return alb, ecs


def build_ecs_conf(alb_security_group_id, common_conf):
    return ECSConfigs(
        cluster=f"{common_conf.project_name}-{common_conf.env_slug}",
        instance_group_name=f"{common_conf.project_name}-{common_conf.env_slug}",
        cloudwatch_prefix=f"{common_conf.project_name}-{common_conf.env_slug}",
        alb_security_group_id=alb_security_group_id,
    )


def get_project_details(
    creds: AwsCredentials, common_conf: GeneralConfiguration, alb_conf: ALBConfigs,
):
    """Retrieves terraform output for project components."""
    alb = get_alb_details(creds, common_conf, alb_conf)
    ecs_conf = build_ecs_conf(alb["alb_security_group_id"]["value"], common_conf)
    ecs = get_ecs_cluster_details(creds, common_conf, ecs_conf)
    return dict(alb=alb, ecs=ecs)


def destroy_environment(
    creds: AwsCredentials, common_conf: GeneralConfiguration, env_conf: EnvConfigs,
):
    """Removes ECS environment."""
    # todo make this work
    logger.info("Get network details")
    network = get_network_details(creds, common_conf)

    common_conf_with_vpc = common_conf._replace(vpc_id=network["vpc_id"]["value"])

    logger.info("Removing ECS cluster")
    destroy_ecs_cluster(creds, common_conf_with_vpc, env_conf.ecs)
    logger.info("Removed ECS cluster")

    logger.info("Removing alb")
    destroy_alb(creds, common_conf_with_vpc, env_conf.alb)
    logger.info("Removed alb")

    # logger.info("Get route 53 details")
    # route53 = get_r53_details(creds, common_conf, env_conf.route53)
    # logger.info("Removing acm certificate")
    # destroy_acm(
    #     creds,
    #     common_conf,
    #     SSLConfigs(
    #         domain_name=env_conf.domain,
    #         zone_id=route53["primary_zone_id"]["value"],
    #     ),
    # )
    # logger.info("Removed acm certificate")

    logger.info("Removing route 53")
    destroy_route53(creds, common_conf, env_conf.route53)
    logger.info("Removed route53 domain: %s", env_conf.domain)

    logger.info(
        "Removed environment: run_id=%s project_name=%s environment=%s",
        common_conf.run_id,
        common_conf.project_name,
        common_conf.env_name,
    )
