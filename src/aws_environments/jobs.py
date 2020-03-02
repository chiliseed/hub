from datetime import datetime, timedelta, timezone

from celery import shared_task
from celery.utils.log import get_task_logger

from infra_executors.alb import HTTP
from infra_executors.build_worker import (
    BuildWorkerConfigs,
    launch_build_worker_server,
    remove_build_worker_server,
)
from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs_environment import create_global_parts, launch_project_infra
from infra_executors.ecs_service import (
    create_acm_for_service,
    launch_infa_for_service,
    destroy_service_infra,
)
from infra_executors.route53 import Route53Configuration
from infra_executors.utils import get_boto3_client
from .constants import InfraStatus
from .models import (
    Environment,
    EnvironmentConf,
    ExecutionLog,
    Project,
    ProjectConf,
    Service,
    ServiceConf,
    BuildWorker,
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
                ecs_executor_role_arn=ecs_cluster["ecs_executor_role_arn"]["value"],
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
def launch_build_worker(build_worker_id, exec_log_id):
    logger.info(
        "Launching build worker for build_worker_id=%s exec_log_id=%s",
        build_worker_id,
        exec_log_id,
    )
    worker = BuildWorker.objects.select_related(
        "service", "service__project", "service__project__environment"
    ).get(id=build_worker_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    creds = worker.service.project.environment.get_creds()
    common_conf = worker.service.project.get_common_conf(exec_log_id, worker.service_id)
    build_worker_conf = BuildWorkerConfigs(
        ssh_key_name=worker.service.project.get_ssh_key_name(),
        aws_access_key_id=creds.access_key,
        aws_access_key_secret=creds.secret_key,
        env_name=worker.service.project.environment.name,
        code_version=exec_log.get_params()["version"],
        service_name=worker.service.name,
        ecr_url=worker.service.conf().ecr_repo_url,
        valid_until=(datetime.utcnow() + timedelta(minutes=5))
        .replace(tzinfo=timezone.utc)
        .isoformat(),
    )

    try:
        infra = launch_build_worker_server(creds, common_conf, build_worker_conf)
        ec2_client = get_boto3_client("ec2", creds)
        waiter = ec2_client.get_waiter("instance_status_ok")
        waiter.wait(
            InstanceIds=[infra["instance_id"]["value"]],
            Filters=[{"Name": "instance-state-code", "Values": ["16"]}],
            WaiterConfig={"Delay": 15, "MaxAttempts": 20,},
        )
    except:
        logger.exception(
            "Failed to launch build worker build_worker_id=%s exec_log_id=%s",
            build_worker_id,
            exec_log_id,
        )

        exec_log.mark_result(False)
        return False

    worker.launched_at = datetime.utcnow().replace(tzinfo=timezone.utc)
    worker.instance_id = infra["instance_id"]["value"]
    worker.public_ip = infra["instance_public_ip"]["value"]
    worker.ssh_key_name = worker.service.project.get_ssh_key_name()
    worker.save()

    exec_log.mark_result(True)

    logger.info(
        "Launched build worker build_worker_id=%s exec_log_id=%s",
        worker.id,
        exec_log_id,
    )
    return True


@shared_task
def remove_build_worker(build_worker_id, exec_log_id):
    logger.info(
        "Remove build worker for build_worker_id=%s exec_log_id=%s",
        build_worker_id,
        exec_log_id,
    )
    worker = BuildWorker.objects.select_related(
        "service", "service__project", "service__project__environment"
    ).get(id=build_worker_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    creds = worker.service.project.environment.get_creds()
    common_conf = worker.service.project.get_common_conf(exec_log_id, worker.service_id)
    build_worker_conf = BuildWorkerConfigs(
        ssh_key_name=worker.service.project.get_ssh_key_name(),
        aws_access_key_id=creds.access_key,
        aws_access_key_secret=creds.secret_key,
        env_name=worker.service.project.environment.name,
        code_version="",
        service_name=worker.service.name,
        ecr_url=worker.service.conf().ecr_repo_url,
        valid_until=(datetime.utcnow() + timedelta(minutes=5))
        .replace(tzinfo=timezone.utc)
        .isoformat(),
    )

    try:
        remove_build_worker_server(creds, common_conf, build_worker_conf)
    except:
        logger.exception(
            "Failed to remove build worker build_worker_id=%s exec_log_id=%s",
            build_worker_id,
            exec_log_id,
        )

        exec_log.mark_result(False)
        return False

    worker.is_deleted = True
    worker.deleted_at = datetime.utcnow().replace(tzinfo=timezone.utc)
    worker.save()

    exec_log.mark_result(True)

    logger.info(
        "Removed build worker build_worker_id=%s exec_log_id=%s",
        worker.id,
        exec_log_id,
    )
    return True
