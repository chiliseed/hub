from celery import shared_task
from celery.utils.log import get_task_logger

from infra_executors.alb import HTTP
from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs_environment import create_global_parts, launch_project_infra
from infra_executors.ecs_service import (
    create_acm_for_service,
    ServiceConfiguration,
    launch_infa_for_service,
    destroy_service_infra)
from infra_executors.route53 import Route53Configuration
from .constants import InfraStatus
from .models import (
    Environment,
    EnvironmentConf,
    ExecutionLog,
    Project,
    ProjectConf,
    Service,
    ServiceConf,
)

logger = get_task_logger(__name__)


@shared_task
def create_environment_infra(env_id, exec_log_id):
    logger.info("Creating environment_id=%d, exec_log_id=%d", env_id, exec_log_id)

    env = Environment.objects.get(id=env_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    env_conf = env.conf()
    creds = AwsCredentials(
        access_key=env_conf.access_key_id,
        secret_key=env_conf.access_key_secret,
        region=env.region,
        session_key="",
    )
    common = GeneralConfiguration(
        organization_id=env.organization.id,
        env_id=env.id,
        project_id="",
        service_id="",
        env_name=env.name,
        env_slug=env.slug,
        project_name="",
        run_id=exec_log.id,
        vpc_id="",
    )
    route_53 = Route53Configuration(domain=env.domain, cname_subdomains=[],)
    try:
        network, r53 = create_global_parts(creds, common, route_53)
        env.set_conf(
            EnvironmentConf(
                vpc_id=network["vpc_id"]["value"],
                access_key_id=env_conf.access_key_id,
                access_key_secret=env_conf.access_key_secret,
                r53_zone_id=r53["primary_zone_id"]["value"],
            )
        )

        env.set_status(InfraStatus.ready)
        exec_log.mark_result(True)

        logger.info(
            "Created environment environment_id=%d, exec_log_id=%d", env_id, exec_log_id
        )
        return True
    except:
        logger.exception(
            "Failed to create environment environment_id=%d, exec_log_id=%d",
            env_id,
            exec_log_id,
        )

        env.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False


@shared_task
def create_project_infra(project_id, exec_log_id):
    logger.info(
        "Creating project environment for project_id=%s exec_log_id=%s",
        project_id,
        exec_log_id,
    )

    project = Project.objects.select_related("environment").get(id=project_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    try:

        creds = project.environment.get_creds()
        common = project.get_common_conf(exec_log.slug)

        alb, ecs_cluster = launch_project_infra(creds, common)

        project.set_conf(
            ProjectConf(
                alb_name=alb["alb_name"]["value"],
                alb_public_dns=alb["public_dns"]["value"],
                ecs_cluster=ecs_cluster["cluster"]["value"],
            )
        )

        project.set_status(InfraStatus.ready)
        exec_log.mark_result(True)

        logger.info(
            "Created project environment project_id=%s exec_log_id=%s",
            project_id,
            exec_log_id,
        )
        return True
    except:
        logger.exception(
            "Failed to create project infra project_id=%s exec_log_id=%s",
            project_id,
            exec_log_id,
        )

        project.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False


@shared_task
def create_service_infra(service_id, exec_log_id):
    logger.info(
        "Creating service environment for service_id=%s exec_log_id=%s",
        service_id,
        exec_log_id,
    )

    service = Service.objects.select_related("project", "project__environment").get(
        id=service_id
    )
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    creds = service.project.environment.get_creds()
    common_conf = service.project.get_common_conf(exec_log_id, service_id)
    r53_conf = service.project.get_r53_conf()

    try:
        acm_arn = create_acm_for_service(
            creds, common_conf, r53_conf, service.subdomain, service.project.environment.conf().r53_zone_id
        )

        ecr_repo_name = f"{service.project.name}/{service.name}"
        service.set_conf(ServiceConf(
            acm_arn=acm_arn,
            health_check_protocol=HTTP,
            ecr_repo_name=f"{service.project.name}/{service.name}"
        ))

        alb_conf = service.project.get_alb_conf()
        ecr_conf = service.project.get_ecr_conf()

        infra = launch_infa_for_service(
            creds, common_conf, r53_conf, alb_conf, ecr_conf,
        )

        ecr_repo_url = [url for url in infra["ecr"]["repositories_urls"]["value"] if ecr_repo_name in url][0]
    except:
        logger.exception(
            "Failed to create project infra project_id=%s exec_log_id=%s",
            service_id,
            exec_log_id,
        )

        service.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False

    service.set_conf(
        ServiceConf(
            acm_arn=acm_arn,
            health_check_protocol=HTTP,
            ecr_repo_name=ecr_repo_name,
            ecr_repo_url=ecr_repo_url,
        )
    )
    service.set_status(InfraStatus.ready)

    exec_log.mark_result(True)

    logger.info(
        "Created service environment service_id=%s exec_log_id=%s",
        service_id,
        exec_log_id,
    )
    return True


@shared_task
def remove_service_infra(service_id, exec_log_id):
    logger.info(
        "Removing service environment for service_id=%s exec_log_id=%s",
        service_id,
        exec_log_id,
    )

    service = Service.objects.select_related("project", "project__environment").get(
        id=service_id
    )
    service.is_deleted = True
    service.save(update_fields=["is_deleted"])

    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    creds = service.project.environment.get_creds()
    common_conf = service.project.get_common_conf(exec_log_id, service_id)
    r53_conf = service.project.get_r53_conf()
    alb_conf = service.project.get_alb_conf()
    ecr_conf = service.project.get_ecr_conf()

    try:
        destroy_service_infra(
            creds, common_conf, r53_conf, alb_conf, ecr_conf, service.project.environment.conf().r53_zone_id, service.subdomain
        )
    except:
        logger.exception(
            "Failed to update project infra project_id=%s exec_log_id=%s",
            service_id,
            exec_log_id,
        )

        service.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False

    exec_log.mark_result(True)

    logger.info(
        "Removed service environment service_id=%s exec_log_id=%s",
        service_id,
        exec_log_id,
    )
    return True
