from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.constants import InfraStatus
from aws_environments.models import Environment, ExecutionLog, EnvironmentConf
from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs_environment import create_global_parts
from infra_executors.route53 import Route53Configuration


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
