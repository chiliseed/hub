from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.constants import InfraStatus
from aws_environments.jobs.deployment import (
    get_deployment_conf,
    deploy_version_to_service,
)
from aws_environments.models import (
    Service,
    ExecutionLog,
    ServiceConf,
    ServiceDeployment,
)
from infra_executors.alb import HTTP
from infra_executors.deploy_ecs_service import remove_ecs_service
from infra_executors.ecs_service import (
    create_acm_for_service,
    launch_infa_for_service,
    destroy_service_infra,
)

logger = get_task_logger(__name__)


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

    if not service.has_web_interface:
        service.set_status(InfraStatus.ready)
        exec_log.mark_result(True)
        logger.info(
            "Service has no web interface. Skipping. service_id=%s exec_log_id=%s",
            service_id,
            exec_log_id,
        )
        return True

    creds = service.project.environment.get_creds()
    common_conf = service.project.get_common_conf(exec_log_id, service_id)
    r53_conf = service.project.get_r53_conf()

    try:
        acm_arn = create_acm_for_service(
            creds,
            common_conf,
            r53_conf,
            service.subdomain,
            service.project.environment.conf().r53_zone_id,
        )

        ecr_repo_name = f"{service.project.name}/{service.name}"
        service.set_conf(
            ServiceConf(
                acm_arn=acm_arn,
                health_check_protocol=HTTP,
                ecr_repo_name=f"{service.project.name}/{service.name}",
            )
        )

        service.project.refresh_from_db()
        alb_conf = service.project.get_alb_conf()
        ecr_conf = service.project.get_ecr_conf()

        infra = launch_infa_for_service(
            creds, common_conf, r53_conf, alb_conf, ecr_conf,
        )

        ecr_repo_url = [
            url
            for url in infra["ecr"]["repositories_urls"]["value"]
            if ecr_repo_name in url
        ][0]
        target_group_arn = [
            arn
            for arn in infra["alb"]["target_groups_arn"]["value"]
            if service.name in arn
        ][0]
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
            target_group_arn=target_group_arn,
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
            creds,
            common_conf,
            r53_conf,
            alb_conf,
            ecr_conf,
            service.project.environment.conf().r53_zone_id,
            service.subdomain,
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


@shared_task
def update_service_infra(previous_service_id, new_service_id, exec_log_id):
    deployment = ServiceDeployment.objects.filter(
        service_id=previous_service_id
    ).latest("deployed_at")

    if not deployment.service.has_web_interface:
        logger.info(
            "Service has no web interface. No changes to apply to infra. "
            "previous_service_id=%s service_id=%s exec_log_id=%s",
            previous_service_id,
            new_service_id,
            exec_log_id,
        )
        exec_log = ExecutionLog.objects.get(id=exec_log_id)
        deployment.service.set_status(InfraStatus.ready)
        exec_log.mark_result(True)
        return

    if deployment:
        creds = deployment.service.project.environment.get_creds()
        remove_ecs_service(creds, get_deployment_conf(deployment))

    remove_service_infra(previous_service_id, exec_log_id)
    create_service_infra(new_service_id, exec_log_id)

    if deployment:
        deploy_version_to_service(deployment.id, exec_log_id)

    return True
