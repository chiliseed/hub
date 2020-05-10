from django.db import transaction
from rest_framework import status
from rest_framework.response import Response


from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.viewsets import ModelViewSet

from aws_environments.constants import InfraStatus
from aws_environments.jobs import create_statics_bucket, launch_database, launch_cache
from aws_environments.models import (
    Project,
    Resource,
    Environment,
    ResourceConf,
    ExecutionLog,
    Service,
)
from aws_environments.serializers import (
    CreateDatabaseSerializer,
    CreateS3BucketSerializer,
    ResourceSerializer,
)
from common.crypto import get_uuid_hex


class CreateDatabaseResource(GenericAPIView):
    serializer_class = CreateDatabaseSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "env_slug"

    def get_queryset(self):
        return Environment.objects.filter(organization=self.request.user.organization)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["organization"] = self.request.user.organization
        return ctx

    def post(self, request, *args, **kwargs):
        environment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resource, created = Resource.objects.get_or_create(
            organization=environment.organization,
            environment=environment,
            project=serializer.validated_data["project"],
            name=serializer.validated_data["name"],
            kind=Resource.Types.db,
            preset=serializer.validated_data["preset"],
            engine=serializer.validated_data["engine"],
        )
        if not created:
            exec_log = ExecutionLog.objects.filter(
                organization=environment.organization,
                action=ExecutionLog.ActionTypes.create,
                component_id=resource.id,
                component=ExecutionLog.Components.resource,
            ).latest("created_at")
            return Response(data=dict(log=exec_log.slug, resource=resource.slug))

        resource.set_identifier(serializer.validated_data["name"], environment)

        preset = Resource.DB_PRESETS[resource.preset]
        engine_defaults = Resource.ENGINE_DEFAULTS[resource.engine]
        resource_conf = ResourceConf(
            instance_type=preset.instance_type,
            engine=serializer.validated_data["engine"],
            engine_version=engine_defaults.engine_version,
            allocated_storage=preset.allocated_storage,
            username=serializer.validated_data["username"],
            password=get_uuid_hex(20),
            port=engine_defaults.port,
        )
        resource.set_conf(resource_conf)
        resource.set_status(InfraStatus.changes_pending, request.user)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.resource,
            resource.id,
        )

        launch_database.delay(resource.id, exec_log.id)

        return Response(
            data=dict(log=exec_log.slug, resource=resource.slug),
            status=status.HTTP_201_CREATED,
        )


class CreateCacheResource(GenericAPIView):
    serializer_class = CreateDatabaseSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "env_slug"

    def get_queryset(self):
        return Environment.objects.filter(organization=self.request.user.organization)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        environment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resource, created = Resource.objects.get_or_create(
            organization=environment.organization,
            environment=environment,
            project=serializer.validated_data["project"],
            name=serializer.validated_data["name"],
            kind=Resource.Types.cache,
            preset=serializer.validated_data["preset"],
            engine=serializer.validated_data["engine"],
        )
        if not created:
            exec_log = ExecutionLog.objects.filter(
                organization=environment.organization,
                action=ExecutionLog.ActionTypes.create,
                component_id=resource.id,
                component=ExecutionLog.Components.resource,
            ).latest("created_at")
            return Response(data=dict(log=exec_log.slug, resource=resource.slug))

        resource.set_identifier(serializer.validated_data["name"], environment)

        preset = Resource.CACHE_PRESETS[resource.preset]
        engine_defaults = Resource.ENGINE_DEFAULTS[resource.engine]
        resource_conf = ResourceConf(
            instance_type=preset.instance_type,
            engine=serializer.validated_data["engine"],
            engine_version=engine_defaults.engine_version,
            port=engine_defaults.port,
            number_of_nodes=preset.number_of_nodes,
            password=get_uuid_hex(15),
        )
        resource.set_conf(resource_conf)
        resource.set_status(InfraStatus.changes_pending, request.user)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.resource,
            resource.id,
        )

        launch_cache.delay(resource.id, exec_log.id)

        return Response(
            data=dict(log=exec_log.slug, resource=resource.slug),
            status=status.HTTP_201_CREATED,
        )


class CreateStaticsBucket(GenericAPIView):
    serializer_class = CreateS3BucketSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "service_slug"

    def get_queryset(self):
        return Service.objects.filter(
            is_deleted=False, organization=self.request.user.organization,
        )

    def post(self, request, *arg, **kwargs):
        service = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resource, created = Resource.objects.get_or_create(
            organization=service.organization,
            environment=service.environment,
            project=service.project,
            service=service,
            name=serializer.validated_data["name"],
            kind=Resource.Types.bucket,
            preset=Resource.Presets.statics,
            engine=Resource.EngineTypes.s3,
        )

        if not created:
            exec_log = ExecutionLog.objects.filter(
                organization=service.organization,
                action=ExecutionLog.ActionTypes.create,
                component_id=resource.id,
                component=ExecutionLog.Components.resource,
            ).latest("created_at")
            return Response(data=dict(log=exec_log.slug, resource=resource.slug))

        resource.set_identifier(serializer.validated_data["name"], service.environment)

        resource.set_status(InfraStatus.changes_pending, request.user)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.create,
            request.data,
            ExecutionLog.Components.resource,
            resource.id,
        )

        create_statics_bucket.delay(resource.id, exec_log.id)

        return Response(
            data=dict(log=exec_log.slug, resource=resource.slug),
            status=status.HTTP_201_CREATED,
        )


class Resources(ModelViewSet):
    serializer_class = ResourceSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return Resource.objects.filter(
            is_deleted=False, organization=self.request.user.organization
        )


class ProjectResources(ModelViewSet):
    serializer_class = ResourceSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "project_slug"

    def get_queryset(self):
        project = self.get_object()
        params = dict(
            project=project,
            is_deleted=False,
            organization=self.request.user.organization
        )

        if "kind" in self.request.query_params:
            params["kind"] = self.request.query_params["kind"]
        if "identifier" in self.request.query_params:
            params["identifier"] = self.request.query_params["identifier"]

        return Resource.objects.filter(**params)

    def get_object(self):
        return get_object_or_404(
            Project,
            is_deleted=False,
            organization=self.request.user.organization,
            slug=self.kwargs[self.lookup_url_kwarg],
        )
