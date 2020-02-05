from rest_framework import serializers

from aws_environments.models import Environment


class CreateEnvironmentSerializer(serializers.ModelSerializer):
    access_key = serializers.CharField(max_length=100)
    access_key_secret = serializers.CharField(max_length=100)

    class Meta:
        model = Environment
        fields = ("name", "domain", "region", "access_key", "access_key_secret")

    def create(self, validated_data):
        payload = {
            **validated_data,
            'organization': self.context['user'].organization,
        }
        payload["configuration"] = Environment.CONF(
            vpc_id="",
            access_key_id=payload.pop("access_key"),
            access_key_secret=payload.pop("access_key_secret"),
            r53_zone_id="",
        ).to_str()
        return super().create(payload)

    # todo add validation of access key and secret


class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ("slug", "name", "region", "domain")
