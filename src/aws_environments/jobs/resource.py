from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.constants import InfraStatus
from aws_environments.models import Resource, ExecutionLog, ResourceConf
from infra_executors.database import DBConfigs, create_postgresql

logger = get_task_logger(__name__)


@shared_task
def launch_database(resource_id, exec_log_id):
    logger.info("Launching new database. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)

    resource = Resource.objects.get(id=resource_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    resource_conf = resource.conf()

    infra_conf = DBConfigs(
        identifier=resource.identifier,
        name=resource.name,
        username=resource_conf.username,
        password=resource_conf.password,
        instance_type=resource_conf.instance_type,
        allocated_storage=resource_conf.allocated_storage,
    )
    creds = resource.environment.get_creds()
    params = resource.project.get_common_conf(exec_log_id)

    try:
        db_infra = create_postgresql(creds, params, infra_conf)
    except Exception:
        logger.exception("Failed to launch database. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
        resource.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False

    resource.set_conf(
        ResourceConf(
            instance_type=resource_conf.instance_type,
            allocated_storage=resource_conf.allocated_storage,
            username=resource_conf.username,
            password=resource_conf.password,
            address=db_infra["master_instance_endpoint"]['value'],
            port=5432,
        )
    )

    resource.set_status(InfraStatus.ready)
    exec_log.mark_result(True)

    logger.info("DB launched. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
    return True
