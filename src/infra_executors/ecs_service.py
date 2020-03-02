"""Manages service infra."""
from typing import NamedTuple

from infra_executors.acm import create_acm, SSLConfigs, destroy_acm
from infra_executors.alb import ALBConfigs, create_alb
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
    r53_zone_id: str,
):
    """Creates acm certificate for service subdomain."""
    logger.info("Setting up acm certificate")
    acm = create_acm(
        creds,
        common_conf,
        SSLConfigs(
            domain_name=f"{subdomain}.{route53_conf.domain}", zone_id=r53_zone_id,
        ),
    )
    logger.info("Created acm certificate: %s", acm["this_acm_certificate_arn"]["value"])
    return acm["this_acm_certificate_arn"]["value"]


def launch_infa_for_service(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    route53_conf: Route53Configuration,
    alb_conf: ALBConfigs,
    ecr_conf: ECRConfigs,
):
    logger.info("Updating alb - opening ports.")
    alb = create_alb(creds, common_conf, alb_conf)
    logger.info("ALB updated")

    logger.info("Update route 53 with subdomains")
    route53 = create_route53(creds, common_conf, route53_conf)
    logger.info("Created new route53 zone: %s", route53["primary_zone_id"]["value"])

    logger.info("Creating ECR repo for service")
    ecr = create_ecr(creds, common_conf, ecr_conf)
    logger.info("Created ECR repo %s", ecr["repositories_names"]["value"])

    return dict(alb=alb, ecr=ecr)


def destroy_service_infra(
    creds: AwsCredentials,
    common_conf: GeneralConfiguration,
    route53_conf: Route53Configuration,
    alb_conf: ALBConfigs,
    ecr_conf: ECRConfigs,
    r53_zone_id: str,
    subdomain: str,
):
    logger.info("Removing ECR repo for service")
    destroy_ecr(creds, common_conf, ecr_conf)
    logger.info("Removed ECR repo")

    logger.info("Updating alb - removing open ports.")
    alb = create_alb(creds, common_conf, alb_conf)
    logger.info("ALB updated")

    logger.info("Update route 53 - removing subdomains")
    route53 = create_route53(creds, common_conf, route53_conf)
    logger.info("Updated route 53")

    logger.info("Removing ACM and its validation cname in route53")
    destroy_acm(
        creds,
        common_conf,
        SSLConfigs(
            domain_name=f"{subdomain}.{route53_conf.domain}", zone_id=r53_zone_id,
        ),
    )
    logger.info("Removed ACM")
    return dict(alb=alb, route53=route53)
