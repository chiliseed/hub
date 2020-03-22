import logging

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from aws_environments.jobs import deploy_version_to_service
from aws_environments.models import Service, ServiceDeployment, ExecutionLog
from aws_environments.serializers import ServiceDeploymentSerializer


logger = logging.getLogger(__name__)


class DeployService(CreateAPIView):
    serializer_class = ServiceDeploymentSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return Service.objects.select_related("project", "environment").filter(
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
            organization_id=self.request.user.organization_id,
            environment_id=service.environment_id,
            project_id=service.project_id,
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
