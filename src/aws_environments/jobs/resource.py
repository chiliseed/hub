from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.constants import InfraStatus
from aws_environments.models import Resource, ExecutionLog, ResourceConf
from infra_executors.cache import CacheConfigs, create_cache, destroy_cache
from infra_executors.database import DBConfigs, create_postgresql, destroy_postgresql
from infra_executors.ecs_environment import get_project_details

logger = get_task_logger(__name__)


def get_servers_security_group(project, exec_log_id):
    """Utility to get ecs servers security group id."""
    creds = project.environment.get_creds()
    params = project.get_common_conf(exec_log_id)
    project_params = get_project_details(creds, params, project.get_alb_conf())
    return project_params["ecs"]["security_group_id"]["value"]


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
        allowed_security_groups_ids=[get_servers_security_group(resource.project, exec_log_id)],
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
            port=resource_conf.port,
            engine=resource_conf.engine,
            engine_version=resource_conf.engine_version,
        )
    )

    resource.set_status(InfraStatus.ready)
    exec_log.mark_result(True)

    logger.info("DB launched. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
    return True


@shared_task
def remove_database(resource_id, exec_log_id):
    logger.info("Destroying database. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)

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
        destroy_postgresql(creds, params, infra_conf)
    except Exception:
        logger.exception("Failed to destroy database. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
        resource.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False

    resource.mark_deleted()
    exec_log.mark_result(True)

    logger.info("Removed database. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
    return True


def is_instance_type_t1_t2(instance_type):
    """Checks if instance type if in t1/2 groups.

    Parameters
    ----------
    instance_type : str

    Returns
    -------
    bool
    """
    return instance_type.startswith("cache.t1.") or instance_type.startswith("cache.t2.")


@shared_task
def launch_cache(resource_id, exec_log_id):
    logger.info("Launching cache. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)

    resource = Resource.objects.get(id=resource_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    resource_conf = resource.conf()
    creds = resource.environment.get_creds()
    params = resource.project.get_common_conf(exec_log_id)

    try:
        infra_conf = CacheConfigs(
            identifier=resource.identifier,
            name=resource.name,
            instance_type=resource_conf.instance_type,
            engine=resource_conf.engine,
            engine_version=resource_conf.engine_version,
            number_of_nodes=resource_conf.number_of_nodes,
            allowed_security_groups_ids=[get_servers_security_group(resource.project, exec_log_id)],
            snapshot_retention_limit_days=0 if is_instance_type_t1_t2(resource_conf.instance_type) else 1,
            apply_immediately=True
        )
        cache_infra = create_cache(creds, params, infra_conf)
    except Exception:
        logger.exception("Failed to launch cache. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
        resource.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False

    resource.set_conf(
        ResourceConf(
            instance_type=resource_conf.instance_type,
            allocated_storage=resource_conf.allocated_storage,
            username=resource_conf.username,
            password=resource_conf.password,
            address=cache_infra["cache_nodes_details"]['value'][0]["address"],
            port=resource_conf.port,
            engine=resource_conf.engine,
            engine_version=resource_conf.engine_version,
        )
    )

    resource.set_status(InfraStatus.ready)
    exec_log.mark_result(True)
    logger.info("Launched cache: %s resource_id=%s exec_log_id=%s", resource_conf.engine, resource_id, exec_log_id)
    return True


@shared_task
def remove_cache(resource_id, exec_log_id):
    logger.info("Remove cache. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)

    resource = Resource.objects.get(id=resource_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    resource_conf = resource.conf()
    creds = resource.environment.get_creds()
    params = resource.project.get_common_conf(exec_log_id)

    try:
        infra_conf = CacheConfigs(
            identifier=resource.identifier,
            name=resource.name,
            instance_type=resource_conf.instance_type,
            engine=resource_conf.engine,
            engine_version=resource_conf.engine_version,
            number_of_nodes=resource_conf.number_of_nodes,
            allowed_security_groups_ids=[get_servers_security_group(resource.project, exec_log_id)],
            snapshot_retention_limit_days=0 if is_instance_type_t1_t2(resource_conf.instance_type) else 1,
            apply_immediately=True
        )
        destroy_cache(creds, params, infra_conf)
    except Exception:
        logger.exception("Failed to destroy cache. resource_id=%s exec_log_id=%s", resource_id, exec_log_id)
        resource.set_status(InfraStatus.error)
        exec_log.mark_result(False)
        return False

    resource.mark_deleted()
    exec_log.mark_result(True)
    logger.info("Removed cache: %s resource_id=%s exec_log_id=%s", resource_conf.engine, resource_id, exec_log_id)
    return True
