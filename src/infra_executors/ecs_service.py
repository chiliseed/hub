import argparse
from typing import NamedTuple, Optional

from infra_executors.acm import create_acm, SSLConfigs, destroy_acm
from infra_executors.alb import ALBConfigs, create_alb, OpenPort, HTTP
from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecr import ECRConfigs, create_ecr, destroy_ecr
from infra_executors.logger import get_logger
from infra_executors.route53 import (
    Route53Configuration,
    create_route53,
    CnameSubDomain,
    get_r53_details,
)

logger = get_logger("ecs-service")


class ServiceConfiguration(NamedTuple):
    name: str
    subdomain: str


def create_acm_for_service(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    route53_conf: Route53Configuration,
    subdomain: str,
):
    """Creates acm certificate for service subdomain."""
    logger.info("Get route 53 details")
    route53 = get_r53_details(creds, common_conf, route53_conf)

    logger.info("Setting up acm certificate")
    acm = create_acm(
        creds,
        common_conf,
        SSLConfigs(
            domain_name=f"{subdomain}.{route53_conf.domain}",
            zone_id=route53["primary_zone_id"]["value"],
        ),
    )
    logger.info("Created acm certificate: %s", acm["this_acm_certificate_arn"]["value"])
    return acm["this_acm_certificate_arn"]["value"]


def launch_infa_for_service(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    service_conf: ServiceConfiguration,
    route53_conf: Route53Configuration,
    alb_conf: ALBConfigs,
    ecr_conf: ECRConfigs,
):
    logger.info("Updating alb - opening ports.")
    alb = create_alb(creds, common_conf, alb_conf)
    logger.info("ALB updated")

    logger.info("Update route 53 with subdomains %s")
    route53_conf = route53_conf._replace(
        cname_subdomains=route53_conf.cname_subdomains
        + [
            CnameSubDomain(
                subdomain=service_conf.subdomain, route_to=alb["public_dns"]["value"],
            )
        ]
    )
    route53 = create_route53(creds, common_conf, route53_conf)
    logger.info("Created new route53 zone: %s", route53["primary_zone_id"]["value"])

    logger.info("Creating ECR repo for service")
    ecr = create_ecr(creds, common_conf, ecr_conf)
    logger.info("Created ECR repo %s", ecr["repositories_names"]["value"])

    return dict(alb=alb, ecr=ecr)


def destroy_service_infra(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    service_conf: ServiceConfiguration,
    route53_conf: Route53Configuration,
):
    logger.info("Removing ECR repo for service")
    ecr_conf = ECRConfigs(
        repositories=[f"{common_conf.project_name}/{service_conf.name}"]
    )
    destroy_ecr(creds, common_conf, ecr_conf)
    logger.info("Removed ECR repo")

    logger.info("Get route 53 details")
    route53 = get_r53_details(creds, common_conf, route53_conf)

    logger.info("Removing ACM and its validation cname in route53")
    destroy_acm(
        creds,
        common_conf,
        SSLConfigs(
            domain_name=route53_conf.domain,
            zone_id=route53["primary_zone_id"]["value"],
        ),
    )
    logger.info("Removed ACM")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/destroy ecs service.")
    parser.add_argument(
        "cmd", type=str, default="create", help="Sub command. One of: create/destroy",
    )
    parser.add_argument(
        "project_name", type=str, help="The name of your project. Example: demo",
    )
    parser.add_argument(
        "environment",
        type=str,
        default="develop",
        help="The name of your environment. Example: dev",
    )
    parser.add_argument(
        "service_name",
        type=str,
        help="The name of the service to launch. Example: api",
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
    common = GeneralConfiguration(args.project_name, args.environment, args.run_id, "")
    cmd_conf = ServiceConfiguration(args.service_name, "demo-api")

    if args.cmd == "create":
        r53_conf = Route53Configuration(domain="chiliseed.com", cname_subdomains=[])
        acm_arn = create_acm_for_service(
            aws_creds, common, r53_conf, cmd_conf.subdomain
        )
        ecr_conf = ECRConfigs(repositories=[f"{common.project_name}/{cmd_conf.name}"])

        launch_infa_for_service(
            aws_creds,
            common,
            cmd_conf,
            r53_conf,
            ALBConfigs(
                alb_name=f"{common.project_name}-{common.env_name}",
                open_ports=[
                    OpenPort(
                        name=args.service_name,
                        container_port=7878,
                        alb_port_http=80,
                        alb_port_https=443,
                        health_check_endpoint="/health/check",
                        health_check_protocol=HTTP,
                        ssl_certificate_arn=acm_arn,
                    )
                ],
            ),
            ecr_conf,
        )
    if args.cmd == "destroy":
        destroy_service_infra(
            aws_creds,
            common,
            cmd_conf,
            Route53Configuration(domain="chiliseed.com", cname_subdomains=[]),
        )
