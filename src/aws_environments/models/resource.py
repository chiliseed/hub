import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Union

from django.contrib.auth import get_user_model
from django.db import models
from fernet_fields import EncryptedTextField

from aws_environments.constants import InfraStatus
from common.models import BaseModel

from .environment import Environment
from .project import Project
from .utils import BaseConf

User = get_user_model()


class ResourceStatus(BaseModel):
    """Manages resource status."""

    resource = models.ForeignKey(
        "Resource", related_name="statuses", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=30, choices=InfraStatus.choices)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Resource #{self.resource.id} | Status {self.status}"


@dataclass
class ResourceConf(BaseConf):
    instance_type: str = ""
    engine: str = ""
    engine_version: str = ""
    number_of_nodes: int = 1
    allocated_storage: int = 5
    username: str = ""
    password: str = ""
    address: str = ""
    port: int = 0


@dataclass
class BucketConf(BaseConf):
    bucket: str
    arn: str
    bucket_domain_name: str
    bucket_regional_domain_name: str
    r53_zone_id: str
    region: str
    website_endpoint: str
    website_domain: str


@dataclass
class DBPreset:
    instance_type: str
    allocated_storage: int


@dataclass
class CachePreset:
    instance_type: str
    number_of_nodes: int


@dataclass
class EngineDefaults:
    port: int
    engine_version: str


class Resource(BaseModel):
    """Manages environment resources such as db and cache."""

    class Types(models.TextChoices):
        db = "database"
        cache = "cache"
        bucket = "bucket"

    class Presets(models.TextChoices):
        dev = "dev"
        prod = "prod"
        statics = "statics"

    class EngineTypes(models.TextChoices):
        postgres = "postgres"
        redis = "redis"
        s3 = "s3"

    ENGINE_DEFAULTS = {
        EngineTypes.postgres: EngineDefaults(5432, "11.6"),
        EngineTypes.redis: EngineDefaults(6379, "5.0.6"),
    }

    DB_PRESETS = {
        Presets.dev: DBPreset("db.t2.medium", 20),
        Presets.prod: DBPreset("db.r4.large", 500),
    }

    CACHE_PRESETS = {
        Presets.dev: CachePreset("cache.t2.small", 1),
        Presets.prod: CachePreset("cache.r5.large", 2),
    }

    organization = models.ForeignKey(
        "organizations.Organization",
        blank=False,
        related_name="aws_resources",
        on_delete=models.CASCADE,
    )
    environment = models.ForeignKey(
        Environment, related_name="resources", on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        Project, related_name="resources", on_delete=models.PROTECT, null=True
    )

    identifier = models.CharField(max_length=150, null=True, blank=True)
    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=50, choices=Types.choices)
    configuration = EncryptedTextField(default="{}")
    preset = models.CharField(max_length=50, choices=Presets.choices)
    engine = models.CharField(max_length=50, choices=EngineTypes.choices)

    last_status = models.ForeignKey(
        ResourceStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="resource_object",
    )

    def __str__(self):
        return f"#{self.id} | Kind: {self.kind} | Identifier: {self.identifier}"

    def set_identifier(self, resource_name, environment):
        """Generate resource identifier string.

        Parameters
        ----------
        resource_name: str
        environment: aws_environments.models.Environment

        Returns
        -------
        str
        """
        self.identifier = f"{environment.name}-{resource_name}-{self.slug}"
        self.save(update_fields=["identifier"])

    def set_status(self, status, actor=None):
        """Change status of a resource."""
        assert status in InfraStatus.values, "Unknown status"
        if actor:
            assert (
                actor.organization == self.organization
            ), "Actor is from another organization"

        status = ResourceStatus(status=status, created_by=actor, resource=self)
        status.save()
        self.last_status = self.statuses.all().order_by("created_at").last()
        self.save(update_fields=["last_status"])

    def conf(self):
        conf_params = json.loads(self.configuration)
        if self.kind in (self.Types.cache, self.Types.db):
            return ResourceConf(**conf_params)
        return BucketConf(**conf_params)

    def set_conf(self, resource_conf: Union[ResourceConf, BucketConf]):
        self.configuration = resource_conf.to_str()
        self.save(update_fields=["configuration"])

    def mark_deleted(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.save(update_fields=["is_deleted", "deleted_at"])
