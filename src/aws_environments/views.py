import logging
from datetime import datetime, timezone

from botocore.exceptions import ClientError
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aws_environments.constants import InfraStatus
from aws_environments.jobs import (
    create_environment_infra,
    create_project_infra,
    create_service_infra,
    launch_build_worker,
    deploy_version_to_service,
    update_service_infra,
)
from aws_environments.models import (
    Environment,
    ExecutionLog,
    Project,
    Service,
    BuildWorker,
    ServiceDeployment,
    EnvironmentVariable,
)
from aws_environments.serializers import (
    CreateEnvironmentSerializer,
    EnvironmentSerializer,
    ExecutionLogSerializer,
    ProjectSerializer,
    ServiceSerializer,
    CreateBuildWorkerSerializer,
    BuildWorkerSerializer,
    ServiceDeploymentSerializer,
    EnvironmentVariableSerializer,
)
from aws_environments.utils import check_if_service_can_be_created
from infra_executors.utils import get_boto3_client

logger = logging.getLogger(__name__)


class EnvironmentCreate(CreateAPIView):
    serializer_class = CreateEnvironmentSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        return ctx

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        env = serializer.save()
        env.set_status(InfraStatus.changes_pending, request.user)
        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.environment,
            env.id,
        )

        create_environment_infra.delay(env.id, exec_log.id)

        return Response(
            dict(env=EnvironmentSerializer(env).data, log=exec_log.slug),
            status=status.HTTP_201_CREATED,
        )


class EnvironmentList(ListAPIView):
    serializer_class = EnvironmentSerializer

    def get_queryset(self):
        params = dict(organization=self.request.user.organization)
        if self.request.query_params.get("name"):
            params["name__iexact"] = self.request.query_params["name"]
        return Environment.objects.filter(**params)


class ExecutionLogDetailsView(RetrieveAPIView):
    serializer_class = ExecutionLogSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return ExecutionLog.objects.filter(organization=self.request.user.organization)


class CreateListProject(ModelViewSet):
    serializer_class = ProjectSerializer
    lookup_url_kwarg = "env_slug"
    lookup_field = "slug"

    def get_queryset(self):
        return Environment.objects.filter(organization=self.request.user.organization)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        env = self.get_object()
        if not env.is_ready():
            return Response(
                data={"detail": "Environment is not in ready state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.save(
            environment=env, organization=self.request.user.organization
        )
        project.set_status(InfraStatus.changes_pending, request.user)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.project,
            project.id,
        )

        create_project_infra.delay(project.id, exec_log.id)

        return Response(
            dict(
                project=self.get_serializer_class()(instance=project).data,
                log=exec_log.slug,
            ),
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        env = self.get_object()
        params = dict(environment=env)
        if request.query_params.get("name"):
            params["name__iexact"] = self.request.query_params["name"]
        return Response(
            data=self.get_serializer_class()(
                instance=Project.objects.filter(**params), many=True
            ).data,
            status=status.HTTP_200_OK,
        )


class CreateListUpdateServices(ModelViewSet):
    serializer_class = ServiceSerializer
    lookup_url_kwarg = "project_slug"
    lookup_field = "slug"

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        ctx["project"] = self.get_object()
        return ctx

    def get_queryset(self):
        return Project.objects.filter(organization=self.request.user.organization)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        project = self.get_object()
        if not project.is_ready():
            return Response(
                data={"detail": "Project is not in ready state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_valid, error_reason = check_if_service_can_be_created(
            serializer.validated_data, project
        )
        if not is_valid:
            return Response(
                data=dict(detail=error_reason), status=status.HTTP_400_BAD_REQUEST
            )

        service = serializer.save(project=project)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.service,
            service.id,
        )

        create_service_infra.delay(service.id, exec_log.id)

        return Response(
            dict(
                service=self.get_serializer_class()(instance=service).data,
                log=exec_log.slug,
            ),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        if not project.is_ready():
            return Response(
                data={"detail": "Project is not in ready state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = {**request.data}
        if not payload.get("slug"):
            return Response(
                data={"detail": "Missing service slug"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_service_slug = payload["slug"]
        old_service = Service.objects.filter(
            slug=old_service_slug, is_deleted=False
        ).first()
        if not old_service:
            return Response(
                data={"detail": "Service not found"}, status=status.HTTP_404_NOT_FOUND,
            )

        del payload["slug"]

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        service = serializer.save(project=project)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.service,
            service.id,
        )

        update_service_infra.delay(old_service.id, service.id, exec_log.id)

        return Response(
            dict(
                service=self.get_serializer_class()(instance=service).data,
                log=exec_log.slug,
            ),
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        params = dict(project=self.get_object(), is_deleted=False)
        if request.query_params.get("name"):
            params["name__iexact"] = self.request.query_params["name"]
        return Response(
            data=self.get_serializer_class()(
                instance=Service.objects.filter(**params), many=True
            ).data,
            status=status.HTTP_200_OK,
        )


class CreateWorker(CreateAPIView):
    serializer_class = CreateBuildWorkerSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return Service.objects.filter(organization=self.request.user.organization)

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
            is_deleted=False,
        )
        if not created:
            ec2_client = get_boto3_client(
                "ec2", worker.service.project.environment.get_creds()
            )
            try:
                resp = ec2_client.describe_instance_status(
                    Filters=[
                        {
                            "Name": "instance-state-code",
                            "Values": ["16"],
                        },  # running state
                    ],
                    InstanceIds=[worker.instance_id,],
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
            service=service, organization=self.request.user.organization
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


class DeployService(CreateAPIView):
    serializer_class = ServiceDeploymentSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return Service.objects.filter(
            organization=self.request.user.organization, is_deleted=False
        )

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        if not service.is_ready():
            return Response(
                data={"detail": "service is not ready"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deployment = ServiceDeployment.objects.create(
            organization=self.request.user.organization,
            service=service,
            version=serializer.validated_data["version"],
        )
        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.deployment,
            deployment.id,
        )

        deploy_version_to_service.delay(deployment.id, exec_log.id)
        return Response(
            data=dict(deployment=deployment.slug, log=exec_log.slug),
            status=status.HTTP_201_CREATED,
        )


class EnvironmentVariables(ModelViewSet):
    serializer_class = EnvironmentVariableSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return Service.objects.filter(
            organization=self.request.user.organization, is_deleted=False
        )

    def perform_create(self, serializer):
        service = self.get_object()
        serializer.save(organization=self.request.user.organization, service=service)

    def list(self, request, *args, **kwargs):
        service = self.get_object()
        serializer = self.get_serializer(service.env_vars.all(), many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        service = self.get_object()
        env_var = get_object_or_404(
            service.env_vars.all(), slug=self.kwargs["key_slug"]
        )
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(env_var, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        service = self.get_object()
        env_var = get_object_or_404(
            service.env_vars.all(), slug=self.kwargs["key_slug"]
        )
        env_var.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
