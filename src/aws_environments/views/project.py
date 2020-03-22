from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aws_environments.constants import InfraStatus
from aws_environments.jobs import create_project_infra
from aws_environments.models import Environment, ExecutionLog, Project
from aws_environments.serializers import ProjectSerializer


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
