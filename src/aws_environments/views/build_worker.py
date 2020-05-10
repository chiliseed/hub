import logging
from datetime import datetime, timezone

from botocore.exceptions import ClientError
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response

from aws_environments.jobs import launch_build_worker
from aws_environments.models import Service, BuildWorker, ExecutionLog
from aws_environments.serializers import (
    CreateBuildWorkerSerializer,
    BuildWorkerSerializer,
)
from infra_executors.utils import get_boto3_client


logger = logging.getLogger(__name__)


class CreateWorker(CreateAPIView):
    serializer_class = CreateBuildWorkerSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return Service.objects.filter(
            organization=self.request.user.organization
        ).select_related("project", "project__environment")

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        if not service.is_ready():
            return Response(
                data={"detail": "service is not ready"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        worker, created = BuildWorker.objects.get_or_create(
            service=service,
            organization=self.request.user.organization,
            project=service.project,
            is_deleted=False,
        )
        if not created and worker.instance_id:
            ec2_client = get_boto3_client(
                "ec2", service.project.environment.get_creds()
            )
            try:
                resp = ec2_client.describe_instance_status(
                    Filters=[
                        {
                            "Name": "instance-state-code",
                            "Values": ["16"],
                        },  # running state
                    ],
                    InstanceIds=[worker.instance_id, ],
                )
                if len(resp["InstanceStatuses"]) == 1:
                    logger.info("Worker is still alive. worker_id=%s", worker.id)
                    return Response(
                        data=dict(build=worker.slug, log=None),
                        status=status.HTTP_200_OK,
                    )
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                logger.debug("client error: %s", e.response)
                logger.warning("error checking instance status: %s", error_code)

        worker.is_deleted = True
        worker.deleted_at = datetime.utcnow().replace(tzinfo=timezone.utc)
        worker.save(update_fields=["is_deleted", "deleted_at"])

        worker = BuildWorker.objects.create(
            service=service,
            organization=self.request.user.organization,
            project=service.project,
            is_deleted=False,
        )

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.build_worker,
            worker.id,
        )

        launch_build_worker.delay(worker.id, exec_log.id)

        return Response(
            data=dict(build=worker.slug, log=exec_log.slug),
            status=status.HTTP_201_CREATED,
        )


class WorkerDetails(RetrieveAPIView):
    serializer_class = BuildWorkerSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return BuildWorker.objects.filter(organization=self.request.user.organization)
