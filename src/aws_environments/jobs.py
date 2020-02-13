import logging

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs_environment import create_global_parts, launch_project_infra
from infra_executors.route53 import Route53Configuration
from .constants import InfraStatus
from .models import Environment, EnvironmentConf, ExecutionLog, Project, ProjectConf

logger = logging.getLogger(__name__)


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
        env_slug=env.slug,
        project_name="environment",
        env_name=env.name,
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


def create_project_infra(project_id, exec_log_id):
    logger.info(
        "Creating project environment for project_id=%s exec_log_id=%s",
        project_id,
        exec_log_id,
    )

    project = Project.objects.select_related("environment").get(id=project_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    try:

        env_conf = project.environment.conf()
        creds = AwsCredentials(
            access_key=env_conf.access_key_id,
            secret_key=env_conf.access_key_secret,
            region=project.environment.region,
            session_key="",
        )

        common = GeneralConfiguration(
            env_slug=project.environment.slug,
            project_name=project.name,
            env_name=project.environment.name,
            run_id=exec_log.id,
            vpc_id=env_conf.vpc_id,
        )

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
