from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.models import ServiceDeployment, ExecutionLog
from infra_executors.deploy_ecs_service import SecretEnvVar, DeploymentConf, deploy_ecs_service


logger = get_task_logger(__name__)


def get_deployment_conf(deployment):
    service_conf = deployment.service.conf()
    project_conf = deployment.service.project.conf()
    env_vars = []
    for env_var in deployment.service.get_env_vars():
        env_vars.append(SecretEnvVar(**env_var))

    logger.debug("env vars are: {}", env_vars)

    return DeploymentConf(
        ecs_cluster=project_conf.ecs_cluster,
        ecs_executor_role_arn=project_conf.ecs_executor_role_arn,
        service_name=deployment.service.name,
        repo_url=service_conf.ecr_repo_url,
        version=deployment.version,
        container_port=deployment.service.container_port,
        target_group_arn=service_conf.target_group_arn,
        secrets=env_vars,
    )


@shared_task
def deploy_version_to_service(deployment_id, exec_log_id):
    logger.info(
        "Deploying new version to service deployment_id=%s exec_log_id=%s",
        deployment_id,
        exec_log_id,
    )

    deployment = ServiceDeployment.objects.select_related(
        "service", "service__project", "service__project__environment"
    ).get(id=deployment_id)
    exec_log = ExecutionLog.objects.get(id=exec_log_id)

    deploy_conf = get_deployment_conf(deployment)

    try:
        deploy_ecs_service(
            deployment.service.project.environment.get_creds(),
            deployment.service.project.get_common_conf(
                exec_log_id, deployment.service_id
            ),
            deploy_conf,
        )
    except Exception:
        logger.exception("Failed to deploy")
        exec_log.mark_result(False)
        deployment.mark_result(False)
        return False

    exec_log.mark_result(True)
    deployment.mark_result(True)
    logger.info(
        "New version deployed. deployment_id=%s exec_log_id=%s",
        deployment_id,
        exec_log_id,
    )
    return True
