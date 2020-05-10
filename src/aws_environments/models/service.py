from dataclasses import dataclass
from datetime import datetime, timezone
import json

from django.contrib.auth import get_user_model
from django.db import models
from fernet_fields import EncryptedTextField

from aws_environments.constants import InfraStatus
from common.models import BaseModel
from infra_executors.utils import get_boto3_client

from .project import Project
from .environment import Environment
from .utils import BaseConf


User = get_user_model()


@dataclass
class ServiceConf(BaseConf):
    acm_arn: str = ""
    health_check_protocol: str = ""
    ecr_repo_name: str = ""
    ecr_repo_url: str = ""
    target_group_arn: str = ""


class ServiceStatus(BaseModel):
    service = models.ForeignKey(
        "Service", on_delete=models.CASCADE, related_name="statuses"
    )
    status = models.CharField(max_length=30, choices=InfraStatus.choices)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Status {self.status} | Set at: {self.created_at}"


class Service(BaseModel):
    """Manages services running in a project.

    For example, environment `development` can hold a project named `our-smart-delivery-service`
    and this project can consist of `client-api` and `dashboard-api` and `dashboard-frontend`.

    This directly maps to ECS TargetGroup/Service +
    """

    PARTS = (
        "acm",
        "alb",
        "route53",
        "ecr",
    )
    organization = models.ForeignKey(
        "organizations.Organization", related_name="services", on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        related_name="services",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    environment = models.ForeignKey(
        Environment, related_name="services", null=True, on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100, null=False, blank=False)

    has_web_interface = models.BooleanField(default=True)
    default_dockerfile_path = models.CharField(max_length=100, default="Dockerfile")
    default_dockerfile_target = models.CharField(max_length=100, null=True, blank=True)

    subdomain = models.CharField(max_length=50, null=True, blank=True)
    container_port = models.PositiveIntegerField(null=True, blank=True)
    alb_port_http = models.PositiveIntegerField(null=True, blank=True)
    alb_port_https = models.PositiveIntegerField(null=True, blank=True)
    health_check_endpoint = models.CharField(max_length=150, default="/")
    configuration = EncryptedTextField(default="{}")

    last_status = models.ForeignKey(
        ServiceStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="service_object",
    )

    def __str__(self):
        return f"#{self.id} | Name: {self.name} |  Project #{self.project.id}"

    def conf(self) -> ServiceConf:
        return ServiceConf(**json.loads(self.configuration))

    def set_conf(self, service_conf: ServiceConf):
        self.configuration = service_conf.to_str()
        self.save(update_fields=["configuration"])

    def set_status(self, status, actor=None):
        """Change status of service infra."""
        assert status in InfraStatus.values, "Unknown status"
        if actor:
            assert (
                actor.organization == self.project.organization
            ), "Actor is from another organization"

        status = ServiceStatus(status=status, created_by=actor, service=self)
        status.save()
        self.last_status = self.statuses.all().order_by("created_at").last()
        self.save(update_fields=["last_status"])

    def is_ready(self):
        return self.project.is_ready() and self.last_status.status == InfraStatus.ready

    def get_ssm_prefix(self):
        """Returns prefix for parameter store env vars."""
        return f"/{self.project.environment.name}/{self.project.name}/{self.name}/"

    def env_vars_generator(self, client, batch_size=50):
        """Paginate over all env variables for this service in System Manager.

        Parameters
        ----------
        client : boto3.client
        batch_size : int
            optional max results to pull

        Returns
        -------
        list of dict
        """
        get_more = True
        next_token = None
        while get_more:
            request_params = dict(
                ParameterFilters=[
                    {
                        "Key": "Name",
                        "Option": "BeginsWith",
                        "Values": [self.get_ssm_prefix()],
                    }
                ],
                MaxResults=batch_size,
            )
            if next_token:
                request_params["NextToken"] = next_token

            env_vars = client.describe_parameters(**request_params)
            next_token = env_vars.get("NextToken")
            yield env_vars["Parameters"]
            get_more = next_token is not None

    def get_env_vars(self):
        """Get service env vars.

        Returns
        -------
        list of dict
        """
        client = get_boto3_client("ssm", self.project.environment.get_creds())
        env_vars = []
        for parameters in self.env_vars_generator(client):
            for param in parameters:
                param_details = client.get_parameter(
                    Name=param["Name"], WithDecryption=True
                )["Parameter"]
                env_vars.append(
                    dict(
                        name=param["Name"].split("/")[-1],
                        value_from=param["Name"],
                        value=param_details["Value"],
                        arn=param_details["ARN"],
                        kind=param_details["Type"],
                        last_modified=param["LastModifiedDate"],
                    )
                )

        return env_vars


class ServiceDeployment(BaseModel):
    """Manages service deployments."""

    organization = models.ForeignKey(
        "organizations.Organization",
        related_name="service_deployments",
        on_delete=models.CASCADE,
        null=False,
        blank=True,
    )
    service = models.ForeignKey(
        Service,
        related_name="deployments",
        on_delete=models.CASCADE,
        null=False,
        blank=True,
    )
    environment = models.ForeignKey(
        Environment,
        related_name="service_deployments",
        on_delete=models.CASCADE,
        null=True,
    )
    project = models.ForeignKey(
        Project, related_name="service_deployments", on_delete=models.CASCADE, null=True
    )

    deployed_at = models.DateTimeField(null=True, blank=True)
    version = models.CharField(max_length=20, null=False, blank=False)
    is_success = models.NullBooleanField(blank=True)

    def __str__(self):
        return f"#{self.id} | Service: {self.service} | Version: {self.version}"

    def mark_result(self, is_success):
        self.is_success = is_success
        self.deployed_at = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.save(update_fields=["is_success", "deployed_at"])


class BuildWorker(BaseModel):
    """Manages deployment build workers.

    These are short lived spot instances, built from Chiliseed ami, which have
    the tools to build docker image and push it to ECR of the service.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        related_name="service_builders",
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        related_name="builders",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )
    service = models.ForeignKey(
        Service, related_name="build_workers", on_delete=models.CASCADE
    )
    launched_at = models.DateTimeField(null=True)
    instance_id = models.CharField(max_length=80, null=True)
    ssh_key_name = EncryptedTextField(max_length=150, null=False)
    public_ip = EncryptedTextField(max_length=50, default="")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} | Service: {self.service} | Launched at: {self.launched_at}"
