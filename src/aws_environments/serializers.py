from rest_framework import serializers

from aws_environments.models import Environment, ExecutionLog, EnvStatus


class CreateEnvironmentSerializer(serializers.ModelSerializer):
    access_key = serializers.CharField(max_length=100)
    access_key_secret = serializers.CharField(max_length=100)

    class Meta:
        model = Environment
        fields = ("name", "domain", "region", "access_key", "access_key_secret")

    def create(self, validated_data):
        payload = {
            **validated_data,
            'organization_id': self.context['user'].organization_id,
        }
        payload["configuration"] = Environment.CONF(
            vpc_id="",
            access_key_id=payload.pop("access_key"),
            access_key_secret=payload.pop("access_key_secret"),
            r53_zone_id="",
        ).to_str()
        print("create payload is", payload)
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
        fields = ("slug", "name", "region", "domain", "created_at", "updated_at", "last_status")


class ExecutionLogSerializer(serializers.ModelSerializer):
    component_slug = serializers.SerializerMethodField()

    class Meta:
        model = ExecutionLog
        fields = ("slug", "action", "is_success", "ended_at", "component", "component_slug")

    def get_component_slug(self, obj):
        return obj.get_component_obj().slug
