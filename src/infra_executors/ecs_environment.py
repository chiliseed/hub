import argparse
from typing import NamedTuple, Any, Dict

from infra_executors.acm import create_acm, SSLConfigs, destroy_acm
from infra_executors.alb import create_alb, ALBConfigs, destroy_alb
from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs import (
    ECSConfigs,
    create_ecs_cluster,
    destroy_ecs_cluster,
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
    get_r53_details,
)

logger = get_logger("ecs-env")


class EnvConfigs(NamedTuple):
    """Configuration parameters required to create an environment."""

    alb: ALBConfigs
    domain: str
    ecs: ECSConfigs
    route53: Route53Configuration


def create_environment(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    env_conf: EnvConfigs,
) -> Dict[Any, Any]:
    """Create new ECS environment."""
    logger.info(
        "Creating environment network. run_id=%s project_name=%s environment=%s",
        common_conf.run_id,
        common_conf.project_name,
        common_conf.env_name,
    )
    network = create_network(creds, common_conf)
    logger.info("Created new vpc %s", network["vpc_id"])

    common_conf_with_vpc = GeneralConfiguration(
        **common_conf._asdict(), vpc_id=network["vpc_id"]
    )

    logger.info("Creating alb with http")
    alb = create_alb(creds, common_conf_with_vpc, env_conf.alb)
    logger.info("Created alb %s with dns %s", alb["alb_name"], alb["alb_arn"])

    logger.info("Setting up route 53 for the project")
    route53 = create_route53(creds, common_conf, env_conf.route53)
    logger.info("Created new route53 zone: %s", route53["primary_zone_id"])

    logger.info("Setting up acm certificate")
    acm = create_acm(
        creds,
        common_conf,
        SSLConfigs(
            domain_name=env_conf.domain, zone_id=route53["primary_zone_id"]
        ),
    )
    logger.info(
        "Created acm certificate: %s", acm["this_acm_certificate_arn"]
    )

    logger.info("Launching ECS cluster")
    ecs = create_ecs_cluster(creds, common_conf_with_vpc, env_conf.ecs)
    logger.info("Created ECS cluster %s", ecs["cluster"])

    return dict(network=network, alb=alb, route53=route53, acm=acm, ecs=ecs,)


def destroy_environment(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    env_conf: EnvConfigs,
):
    """Removes ECS environment."""
    logger.info("Get route 53 details")
    route53 = get_r53_details(creds, common_conf, env_conf.route53)
    logger.info("Get network details")
    network = get_network_details(creds, common_conf)

    common_conf_with_vpc = common_conf._replace(
        vpc_id=network["vpc_id"]["value"]
    )

    logger.info("Removing ECS cluster")
    destroy_ecs_cluster(creds, common_conf_with_vpc, env_conf.ecs)
    logger.info("Removed ECS cluster")

    logger.info("Removing alb")
    destroy_alb(creds, common_conf_with_vpc, env_conf.alb)
    logger.info("Removed alb")

    logger.info("Removing acm certificate")
    destroy_acm(
        creds,
        common_conf,
        SSLConfigs(
            domain_name=env_conf.domain,
            zone_id=route53["primary_zone_id"]["value"],
        ),
    )
    logger.info("Removed acm certificate")

    logger.info("Removing route 53")
    destroy_route53(creds, common_conf, env_conf.route53)
    logger.info("Removed route53 domain: %s", env_conf.domain)

    logger.info(
        "Removed environment: run_id=%s project_name=%s environment=%s",
        common_conf.run_id,
        common_conf.project_name,
        common_conf.env_name,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create/destroy ecs cluster in the provides vpc."
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
        "domain",
        type=str,
        help="Domain name for the services. Example: example.com",
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
        args.project_name, args.environment, args.run_id, ""
    )

    cmd_configs = EnvConfigs(
        alb=ALBConfigs(
            alb_name=f"{common.project_name}-{common.env_name}",
            ssl_certificate_arn=None,
            open_ports=[],
        ),
        domain=args.domain,
        ecs=ECSConfigs(
            cluster=f"{common.project_name}-{common.env_name}",
            instance_group_name=f"{common.project_name}-{common.env_name}",
            cloudwatch_prefix=f"{common.project_name}-{common.env_name}",
        ),
        route53=Route53Configuration(
            domain=args.domain, cname_subdomains=[],
        ),
    )
    if args.cmd == "create":
        create_environment(aws_creds, common, cmd_configs)
    if args.cmd == "destroy":
        destroy_environment(aws_creds, common, cmd_configs)
