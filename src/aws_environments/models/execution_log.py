import json
from datetime import datetime

import pytz
from django.db import models
from fernet_fields import EncryptedTextField

from common.models import BaseModel

from .environment import Environment
from .project import Project
from .service import BuildWorker, Service, ServiceDeployment
from .resource import Resource


class ExecutionLog(BaseModel):
    """Manages infra executor logs for a specific change."""

    class ActionTypes(models.TextChoices):
        create = "create"
        destroy = "destroy"
        update = "update"
        details = "outputs"

    class Components(models.TextChoices):
        service = "service"
        project = "project"
        environment = "environment"
        build_worker = "build_worker"
        deployment = "deployment"
        resource = "resource"

    organization = models.ForeignKey(
        "organizations.Organization",
        blank=False,
        related_name="aws_runs",
        on_delete=models.CASCADE,
    )

    action = models.CharField(
        max_length=50, choices=ActionTypes.choices, null=False, blank=False
    )
    is_success = models.NullBooleanField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # specific execution params provided by the user
    params = EncryptedTextField(default="{}")

    component = models.CharField(
        max_length=50,
        choices=Components.choices,
        null=False,
        blank=False,
        db_index=True,
    )
    component_id = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )

    @classmethod
    def register(cls, organization, action, params, component, component_id):
        """Create ExecutionLog instance to note a change that much happen."""
        assert action in ExecutionLog.ActionTypes.values, "Unknown action"
        assert component in ExecutionLog.Components.values, "Unknown component"

        return ExecutionLog.objects.create(
            organization=organization,
            action=action,
            params=json.dumps(params),
            component=component,
            component_id=component_id,
        )

    def get_params(self):
        return json.loads(self.params)

    def get_component_obj(self):
        if self.component == self.Components.environment:
            return Environment.objects.get(id=self.component_id)
        if self.component == self.Components.project:
            return Project.objects.get(id=self.component_id)
        if self.component == self.Components.service:
            return Service.objects.get(id=self.component_id)
        if self.component == self.Components.build_worker:
            return BuildWorker.objects.get(id=self.component_id)
        if self.component == self.Components.deployment:
            return ServiceDeployment.objects.get(id=self.component_id)
        if self.component == self.Components.resource:
            return Resource.objects.get(id=self.component_id)
        return None

    def mark_result(self, is_success):
        self.is_success = is_success
        self.ended_at = datetime.utcnow().replace(tzinfo=pytz.UTC)
        self.save(update_fields=["is_success", "ended_at"])
