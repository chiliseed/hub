from datetime import datetime, timedelta, timezone

from celery import shared_task
from celery.utils.log import get_task_logger

from aws_environments.models import BuildWorker, ExecutionLog
from infra_executors.build_worker import (
    BuildWorkerConfigs,
    launch_build_worker_server,
    remove_build_worker_server,
)
from infra_executors.utils import get_boto3_client


logger = get_task_logger(__name__)


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
        dockerfile=worker.service.default_dockerfile_path,
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
        code_version=exec_log.get_params()["version"],
        service_name=worker.service.name,
        dockerfile=worker.service.default_dockerfile_path,
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
