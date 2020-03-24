import json
from dataclasses import dataclass

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
    resource = models.ForeignKey("Resource", related_name="statuses", on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=InfraStatus.choices)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Resource #{self.resource.id} | Status {self.status}"


@dataclass
class ResourceConf(BaseConf):
    instance_type: str
    allocated_storage: int = 5
    username: str = ""
    password: str = ""
    address: str = ""
    port: int = 0


class Resource(BaseModel):
    """Manages environment resources such as db and cache."""

    class Types(models.TextChoices):
        db = "database"
        cache = "cache"

    organization = models.ForeignKey(
        "organizations.Organization",
        blank=False,
        related_name="aws_resources",
        on_delete=models.CASCADE,
    )
    environment = models.ForeignKey(
        Environment, related_name="resources", on_delete=models.CASCADE
    )
    project = models.ForeignKey(Project, related_name="resources", on_delete=models.PROTECT, null=True)

    identifier = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=50, choices=Types.choices)
    configuration = EncryptedTextField(default="{}")

    last_status = models.ForeignKey(
        ResourceStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="resource_object",
    )

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
        return ResourceConf(**json.loads(self.configuration))

    def set_conf(self, resource_conf: ResourceConf):
        self.configuration = resource_conf.to_str()
        self.save(update_fields=["configuration"])
