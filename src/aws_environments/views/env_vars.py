import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aws_environments.models import Service
from aws_environments.serializers import EnvironmentVariableSerializer
from infra_executors.utils import get_boto3_client


logger = logging.getLogger(__name__)


class EnvironmentVariables(ModelViewSet):
    serializer_class = EnvironmentVariableSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return Service.objects.filter(
            organization=self.request.user.organization, is_deleted=False
        ).select_related("project__environment", "project")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = self.get_object()

        client = get_boto3_client("ssm", service.project.environment.get_creds())

        key_name = f"{service.get_ssm_prefix()}{serializer.validated_data['key_name']}"
        logger.info("Adding new variable: %s", key_name)
        client.put_parameter(
            Name=key_name,
            Value=serializer.validated_data["key_value"],
            Type="SecureString"
            if serializer.validated_data.get("is_secure", True)
            else "String",
            Overwrite=True,
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            dict(key_name=key_name), status=status.HTTP_201_CREATED, headers=headers
        )

    def list(self, request, *args, **kwargs):
        service = self.get_object()
        return Response(service.get_env_vars())

    def destroy(self, request, *args, **kwargs):
        if not request.data["key_name"]:
            return Response(
                data=dict(detail="Must provide key name"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = self.get_object()
        client = get_boto3_client("ssm", service.project.environment.get_creds())

        key_name = f"{service.get_ssm_prefix()}{request.data['key_name']}"
        try:
            client.delete_parameter(Name=key_name)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            logger.exception("Failed to delete env vars: %s", key_name)
            return Response(
                data={
                    "detail": "Error deleting key. Does this key exist? Check key name and try again."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
