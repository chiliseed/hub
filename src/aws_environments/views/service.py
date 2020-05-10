from django.db import transaction
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aws_environments.jobs import create_service_infra, launch_database, update_service_infra
from aws_environments.models import Project, ExecutionLog, Resource, Service
from aws_environments.serializers import ServiceSerializer
from aws_environments.utils import check_if_service_can_be_created


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

        service = serializer.save(
            project=project,
            environment=project.environment,
            organization=request.user.organization,
        )

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

    @transaction.atomic
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
        service = serializer.save(
            project=project,
            organization=project.organization,
            environment=project.environment,
        )

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


class AddDB(GenericAPIView):
    lookup_url_kwarg = "service_slug"
    lookup_field = "slug"

    def get_queryset(self):
        return Service.objects.filter(is_deleted=False, organization=self.request.user.organization)

    def post(self, request, *args, **kwargs):
        _service = self.get_object()
        db = Resource.objects.filter(
            organization=self.request.user.organization,
            kind=Resource.Types.db,
            slug=self.request.data["db_slug"]
        ).first()

        if not db:
            return Response(data={"detail": "related resource not found"}, status=status.HTTP_404_NOT_FOUND)

        exec_log = ExecutionLog.register(
            self.request.user.organization,
            ExecutionLog.ActionTypes.update,
            request.data,
            ExecutionLog.Components.resource,
            db.id,
        )

        launch_database.delay(db.id, exec_log.id)
        return Response(data=dict(log=exec_log.slug))
