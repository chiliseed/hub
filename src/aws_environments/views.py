import logging

from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aws_environments.constants import InfraStatus
from aws_environments.jobs import (
    create_environment_infra,
    create_project_infra,
    create_service_infra,
)
from aws_environments.models import Environment, ExecutionLog, Project, Service
from aws_environments.serializers import (
    CreateEnvironmentSerializer,
    EnvironmentSerializer,
    ExecutionLogSerializer,
    ProjectSerializer,
    ServiceSerializer,
)


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


class CreateListServices(ModelViewSet):
    serializer_class = ServiceSerializer
    lookup_url_kwarg = "project_slug"
    lookup_field = "slug"

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
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

    def list(self, request, *args, **kwargs):
        params = dict(project=self.get_object())
        if request.query_params.get("name"):
            params["name__iexact"] = self.request.query_params["name"]
        return Response(
            data=self.get_serializer_class()(
                instance=Service.objects.filter(**params), many=True
            ).data,
            status=status.HTTP_200_OK,
        )

    def can_create(self, request, *args, **kwargs):
        project = self.get_object()
        logger.info("Checking if service can be created")
        serializer = ServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info("Checking if service with this name/subdomain already exists")
        service_exists = Service.objects.filter(
            Q(project=project), Q(is_deleted=False),
            Q(name=serializer.validated_data["name"])
            | Q(subdomain=serializer.validated_data["subdomain"]),
        ).exists()
        is_port_taken = Service.objects.filter(
            Q(project=project), Q(is_deleted=False),
            Q(container_port=serializer.validated_data["container_port"])
            | Q(alb_port_http=serializer.validated_data["alb_port_http"])
            | Q(alb_port_https=serializer.validated_data["alb_port_https"]),
        ).exists()

        if service_exists:
            logger.info(
                "Service with this name/subdomain already exists. name=%s subdomain=%s project_id=%s",
                serializer.validated_data["name"],
                serializer.validated_data["subdomain"],
                project.id,
            )
            response = dict(
                can_create=False,
                reason="Service with this name/subdomain already exists.",
            )
        elif is_port_taken:
            logger.info(
                "Ports are taken. container_port=%s alb_http_port=%s alb_http_ports=%s project_id=%s",
                serializer.validated_data["container_port"],
                serializer.validated_data["alb_port_http"],
                serializer.validated_data["alb_port_https"],
                project.id,
            )
            response = dict(
                can_create=False,
                reason="Your other services for this project already took those ports.",
            )
        else:
            logger.info("OK to create this service. project_id=%s", project.id)
            response = dict(can_create=True, reason=None)
        return Response(data=response, status=status.HTTP_200_OK)
