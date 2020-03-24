import logging

from django.db import transaction
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response

from aws_environments.constants import InfraStatus
from aws_environments.jobs import create_environment_infra
from aws_environments.models import ExecutionLog, Environment
from aws_environments.serializers import CreateEnvironmentSerializer, EnvironmentSerializer, ServiceSerializer

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


class EnvironmentListServices(ListAPIView):
    serializer_class = ServiceSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "env_slug"

    def get_queryset(self):
        environment = Environment.objects.get(slug=self.kwargs["env_slug"])
        return environment.services.filter(is_deleted=False)
