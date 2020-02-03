from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from django.db import IntegrityError, transaction
from djoser.conf import settings as djoser_settings
from rest_framework import serializers

from organizations.models import Organization
from users.models import User


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    organization = serializers.CharField(max_length=100)

    default_error_messages = {
        "cannot_create_user": djoser_settings.CONSTANTS.messages.CANNOT_CREATE_USER_ERROR,
        "password_mismatch": djoser_settings.CONSTANTS.messages.PASSWORD_MISMATCH_ERROR,
    }

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "organization",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["re_password"] = serializers.CharField(
            style={"input_type": "password"}
        )

    def validate(self, attrs):
        self.fields.pop("re_password", None)
        re_password = attrs.pop("re_password")
        organization = attrs.pop("organization")

        user = User(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except DjangoCoreValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error["non_field_errors"]}
            )

        if attrs["password"] != re_password:
            self.fail("password_mismatch")

        attrs["organization"] = organization
        return attrs

    def create(self, validated_data):
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail("cannot_create_user")

        return user

    def perform_create(self, validated_data):
        with transaction.atomic():
            organization = Organization.objects.create(
                name=validated_data["organization"]
            )
            user_data = {
                **validated_data,
                "organization": organization,
                "username": validated_data["email"],
            }
            user = User.objects.create_user(**user_data)
            if djoser_settings.SEND_ACTIVATION_EMAIL:
                user.is_active = False
                user.save(update_fields=["is_active"])
        return user


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("slug", "name")


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("slug", "email", "organization")
        read_only_fields = ("slug",)
