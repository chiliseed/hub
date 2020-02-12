import logging
from datetime import datetime

import pytz

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.ecs_environment import EnvConfigs, create_environment, create_global_parts
from infra_executors.route53 import Route53Configuration
from .models import Environment, EnvStatus, EnvironmentConf, ExecutionLog

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
        vpc_id=""
    )
    route_53 = Route53Configuration(
            domain=env.domain,
            cname_subdomains=[],
        )
    try:
        network, r53 = create_global_parts(creds, common, route_53)
        env.set_conf(EnvironmentConf(
            vpc_id=network['vpc_id']['value'],
            access_key_id=env_conf.access_key_id,
            access_key_secret=env_conf.access_key_secret,
            r53_zone_id=r53["primary_zone_id"]["value"],
        ))

        env.set_status(EnvStatus.Statuses.ready)
        exec_log.is_success = True
        exec_log.ended_at = datetime.utcnow().replace(tzinfo=pytz.UTC)
        exec_log.save(update_fields=["is_success", "ended_at"])
        return True
    except:
        logger.exception("Failed to create environment")

        env.set_status(EnvStatus.Statuses.error)
        exec_log.is_success = False
        exec_log.ended_at = datetime.utcnow().replace(tzinfo=pytz.UTC)
        exec_log.save(update_fields=["is_success", "ended_at"])
        return False
