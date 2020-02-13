from django.db import transaction
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.response import Response

from aws_environments.constants import InfraStatus
from aws_environments.jobs import create_environment_infra, create_project_infra
from aws_environments.models import Environment, ExecutionLog
from aws_environments.serializers import (
    CreateEnvironmentSerializer,
    EnvironmentSerializer,
    ExecutionLogSerializer,
    ProjectSerializer,
)
from control_center.scheduler import scheduler


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

        scheduler.add_job(
            create_environment_infra, args=(env.id, exec_log.id), trigger=None
        )

        return Response(
            dict(env=EnvironmentSerializer(env).data, log=exec_log.slug),
            status=status.HTTP_201_CREATED,
        )


class EnvironmentList(ListAPIView):
    serializer_class = EnvironmentSerializer

    def get_queryset(self):
        return Environment.objects.filter(organization=self.request.user.organization)


class ExecutionLogDetailsView(RetrieveAPIView):
    serializer_class = ExecutionLogSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return ExecutionLog.objects.filter(organization=self.request.user.organization)


class CreateProject(CreateAPIView):
    serializer_class = ProjectSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return Environment.objects.filter(organization=self.request.user.organization)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        env = get_object_or_404(self.get_queryset(), slug=kwargs["env_slug"])

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

        scheduler.add_job(
            create_project_infra, args=(project.id, exec_log.id), trigger=None
        )

        return Response(
            dict(
                project=self.get_serializer_class()(instance=project).data,
                log=exec_log.slug,
            ),
            status=status.HTTP_201_CREATED,
        )
