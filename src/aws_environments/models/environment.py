import json
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import models
from fernet_fields import EncryptedTextField

from aws_environments.constants import InfraStatus, Regions
from common.models import BaseModel
from infra_executors.constants import AwsCredentials
from .utils import BaseConf

from .validators import OptionalSchemeURLValidator

User = get_user_model()


@dataclass
class EnvironmentConf(BaseConf):
    vpc_id: str = ""
    access_key_id: str = ""
    access_key_secret: str = ""
    r53_zone_id: str = ""


class EnvStatus(BaseModel):
    environment = models.ForeignKey(
        "Environment", on_delete=models.CASCADE, related_name="statuses"
    )
    status = models.CharField(max_length=30, choices=InfraStatus.choices)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Environment #{self.environment.id} | Status {self.status}"


class Environment(BaseModel):
    """Manages organization environments.

    Relevant to global parts of ECS environment: vpc/main domain.
    For example:
        environment "development" will build a vpc called "development" where
        the all development services can be launched using chiliseed.
    """

    CONF = EnvironmentConf
    REGIONS = Regions
    PARTS = (
        "network",
        "route53",
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        blank=False,
        related_name="aws_environments",
        on_delete=models.CASCADE,
    )
    last_status = models.ForeignKey(
        EnvStatus, null=True, blank=True, on_delete=models.CASCADE, related_name="env"
    )

    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=200, validators=[OptionalSchemeURLValidator()])
    region = models.CharField(
        max_length=20, choices=REGIONS.choices, default=REGIONS.nvirginia
    )
    configuration = EncryptedTextField(default="{}")

    class Meta:
        unique_together = ["organization_id", "name"]

    def __str__(self):
        return f"#{self.id} | Name: {self.name}"

    def conf(self) -> EnvironmentConf:
        return EnvironmentConf(**json.loads(self.configuration))

    def set_conf(self, conf: EnvironmentConf):
        self.configuration = conf.to_str()
        self.save(update_fields=["configuration"])

    def is_ready(self):
        return self.last_status.status == InfraStatus.ready

    def get_creds(self) -> AwsCredentials:
        conf = self.conf()
        return AwsCredentials(
            access_key=conf.access_key_id,
            secret_key=conf.access_key_secret,
            region=self.region,
            session_key="",
        )

    def set_status(self, status, actor=None):
        """Change status of environment."""
        assert status in InfraStatus.values, "Unknown status"
        if actor:
            assert (
                actor.organization == self.organization
            ), "Actor is from another organization"

        status = EnvStatus(status=status, created_by=actor, environment=self)
        status.save()
        self.last_status = self.statuses.all().order_by("created_at").last()
        self.save(update_fields=["last_status"])
