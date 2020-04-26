import string

from django.core.validators import URLValidator
from rest_framework import serializers

from aws_environments.constants import InfraStatus
from aws_environments.models import (
    BuildWorker,
    Environment,
    EnvStatus,
    ExecutionLog,
    Project,
    ProjectStatus,
    Service,
    ServiceConf,
    ServiceDeployment,
    Resource,
)


class CreateEnvironmentSerializer(serializers.ModelSerializer):
    access_key = serializers.CharField(max_length=100)
    access_key_secret = serializers.CharField(max_length=100)

    class Meta:
        model = Environment
        fields = ("name", "domain", "region", "access_key", "access_key_secret")

    def create(self, validated_data):
        payload = {
            **validated_data,
            "organization_id": self.context["user"].organization_id,
        }
        payload["configuration"] = Environment.CONF(
            vpc_id="",
            access_key_id=payload.pop("access_key"),
            access_key_secret=payload.pop("access_key_secret"),
            r53_zone_id="",
        ).to_str()
        return super().create(payload)

    # todo add validation of access key and secret


class EnvStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvStatus
        fields = ("slug", "status", "created_at")


class EnvironmentSerializer(serializers.ModelSerializer):
    last_status = EnvStatusSerializer()

    class Meta:
        model = Environment
        fields = (
            "slug",
            "name",
            "region",
            "domain",
            "created_at",
            "updated_at",
            "last_status",
        )


class ExecutionLogSerializer(serializers.ModelSerializer):
    component_slug = serializers.SerializerMethodField()

    class Meta:
        model = ExecutionLog
        fields = (
            "slug",
            "action",
            "is_success",
            "ended_at",
            "component",
            "component_slug",
        )

    def get_component_slug(self, obj):
        return obj.get_component_obj().slug


class ProjectStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectStatus
        fields = ("slug", "status", "created_at")


class ProjectSerializer(serializers.ModelSerializer):
    environment = EnvironmentSerializer(read_only=True)
    last_status = ProjectStatusSerializer(read_only=True)

    class Meta:
        model = Project
        fields = (
            "slug",
            "name",
            "environment",
            "last_status",
        )
        read_only_fields = ("slug",)


class ServiceSerializer(serializers.ModelSerializer):
    container_port = serializers.IntegerField(required=True)
    alb_port_http = serializers.IntegerField(required=True)
    alb_port_https = serializers.IntegerField(required=True)
    health_check_endpoint = serializers.CharField(max_length=100, required=True)
    ecr_repo_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = (
            "slug",
            "name",
            "subdomain",
            "container_port",
            "alb_port_http",
            "alb_port_https",
            "health_check_endpoint",
            "ecr_repo_url",
            "has_web_interface",
            "default_dockerfile_path",
        )
        read_only_fields = ("slug",)

    def validate_subdomain(self, value):
        if not value:
            raise serializers.ValidationError("subdomain is required")

        dummy_uri_to_check = f"http://{value}.example.com"
        # this will raise validation errors in case of issues
        URLValidator().__call__(dummy_uri_to_check)

        return value

    def create(self, validated_data):
        payload = {**validated_data}
        payload["name"] = validated_data["name"].translate(
            {ord(c): None for c in string.whitespace}
        )
        payload["configuration"] = ServiceConf(
            acm_arn="", health_check_protocol="", ecr_repo_name="",
        ).to_str()
        service = super().create(payload)
        service.set_status(InfraStatus.changes_pending, self.context["user"])
        return service

    def get_ecr_repo_url(self, obj):
        return obj.conf().ecr_repo_url


class CreateBuildWorkerSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=50, required=True)


class BuildWorkerSerializer(serializers.ModelSerializer):
    is_ready = serializers.SerializerMethodField()
    ssh_key = serializers.SerializerMethodField()

    class Meta:
        model = BuildWorker
        fields = ("slug", "is_ready", "public_ip", "ssh_key", "ssh_key_name")

    def get_is_ready(self, obj):
        return obj.launched_at is not None

    def get_ssh_key(self, obj):
        return obj.service.project.get_ssh_key()


class ServiceDeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceDeployment
        fields = ("slug", "deployed_at", "version", "is_success")
        read_only_fields = ("slug", "deployed_at", "is_success")


class EnvironmentVariableSerializer(serializers.Serializer):
    key_name = serializers.CharField()
    key_value = serializers.CharField()
    is_secret = serializers.BooleanField(default=True)


class CreateDatabaseSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    engine = serializers.ChoiceField(choices=[Resource.EngineTypes.postgres])
    project = serializers.SlugRelatedField(slug_field="slug", queryset=Project.objects.all())

    class Meta:
        model = Resource
        fields = (
            "name",
            "preset",
            "engine",
            "username",
            "project",
        )

    def validate_project(self, obj):
        if obj.organization != self.context["organization"]:
            raise serializers.ValidationError("Project not found")
        return obj


class CreateCacheSerializer(serializers.ModelSerializer):
    engine = serializers.ChoiceField(choices=[Resource.EngineTypes.redis])

    class Meta:
        model = Resource
        fields = (
            "name",
            "preset",
            "engine",
        )


class ResourceSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    configuration = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = (
            "slug",
            "identifier",
            "name",
            "kind",
            "preset",
            "engine",
            "status",
            "configuration",
            "created_at",
            "updated_at",
        )

    def get_status(self, obj):
        return obj.last_status.status

    def get_configuration(self, obj):
        return obj.conf().to_dict()
