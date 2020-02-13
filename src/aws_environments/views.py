from django.db import transaction
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from aws_environments.jobs import create_environment_infra
from aws_environments.models import Environment, EnvStatus, ExecutionLog
from aws_environments.serializers import CreateEnvironmentSerializer, EnvironmentSerializer, ExecutionLogSerializer
from control_center.scheduler import scheduler


class EnvironmentCreate(CreateAPIView):
    serializer_class = CreateEnvironmentSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.request.user
        return ctx

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        env = serializer.save()
        env.set_status(EnvStatus.Statuses.changes_pending, request.user)
        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.environment,
            env.id,
        )

        scheduler.add_job(create_environment_infra, args=(env.id, exec_log.id), trigger=None)

        return Response(dict(env=EnvironmentSerializer(env).data, log=exec_log.slug), status=status.HTTP_201_CREATED)


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


# class CreateProject(CreateAPIView):

