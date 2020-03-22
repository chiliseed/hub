from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.constants import InfraStatus
from aws_environments.models import Project, ExecutionLog, ProjectConf
from infra_executors.ecs_environment import launch_project_infra


logger = get_task_logger(__name__)


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
