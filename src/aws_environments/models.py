import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime

import pytz
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.db import models
from fernet_fields import EncryptedTextField

from aws_environments.constants import Regions, InfraStatus
from common.models import BaseModel
from infra_executors.alb import HTTP, ALBConfigs, OpenPort
from infra_executors.constants import AwsCredentials, GeneralConfiguration, KEYS_DIR
from infra_executors.ecr import ECRConfigs
from infra_executors.route53 import Route53Configuration, CnameSubDomain


User = get_user_model()


class InvalidConfiguration(Exception):
    """Signals bad configuration."""


class OptionalSchemeURLValidator(URLValidator):
    def __call__(self, value):
        if "://" not in value:
            value = "http://" + value
        super().__call__(value)


@dataclass
class EnvironmentConf:
    vpc_id: str
    access_key_id: str
    access_key_secret: str
    r53_zone_id: str

    def to_str(self):
        return json.dumps(asdict(self))


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

    def get_latest_run(self):
        return ExecutionLog.objects.filter(
            component=ExecutionLog.Components.environment, component_id=self.id,
        ).latest("created_at")

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


@dataclass
class ProjectConf:
    alb_name: str
    alb_public_dns: str
    ecs_cluster: str
    ecs_executor_role_arn: str = ""

    def to_str(self):
        return json.dumps(asdict(self))


class ProjectStatus(BaseModel):
    """Track the status of the project infrastructure."""

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="statuses"
    )
    status = models.CharField(max_length=30, choices=InfraStatus.choices)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Environment #{self.project.id} | Status {self.status}"


class Project(BaseModel):
    """Manages projects in AWS environment.

    For example, project `backend-api` can be built in environment `development`,
    as well as project `some-micro-service`

    This directly maps to ECS cluster with ALB.
    """

    PARTS = (
        "alb",
        "ecs",
    )

    last_status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="project_object",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        blank=False,
        related_name="aws_projects",
        on_delete=models.CASCADE,
    )
    environment = models.ForeignKey(
        Environment, related_name="projects", on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100, null=False, blank=False)
    configuration = EncryptedTextField(default="{}")

    class Meta:
        unique_together = ["environment_id", "name"]

    def __str__(self):
        return f"#{self.id} | Env: {self.environment.name} | Name: {self.name}"

    def is_ready(self):
        return (
            self.environment.is_ready() and self.last_status.status == InfraStatus.ready
        )

    def set_conf(self, conf: ProjectConf):
        self.configuration = conf.to_str()
        self.save(update_fields=["configuration"])

    def set_status(self, status, actor=None):
        """Change status of project."""
        assert status in InfraStatus.values, "Unknown status"
        if actor:
            assert (
                actor.organization == self.organization
            ), "Actor is from another organization"

        status = ProjectStatus(status=status, created_by=actor, project=self)
        status.save()
        self.last_status = self.statuses.all().order_by("created_at").last()
        self.save(update_fields=["last_status"])

    def conf(self) -> ProjectConf:
        return ProjectConf(**json.loads(self.configuration))

    def get_common_conf(self, exec_log_id, service_id=None) -> GeneralConfiguration:
        env_conf = self.environment.conf()
        return GeneralConfiguration(
            organization_id=self.organization.id,
            env_id=self.environment_id,
            project_id=self.id,
            service_id=service_id,
            env_name=self.environment.name,
            project_name=self.name,
            run_id=exec_log_id,
            vpc_id=env_conf.vpc_id,
            env_slug=self.environment.slug,
        )

    def get_r53_conf(self) -> Route53Configuration:
        cnames = [
            CnameSubDomain(
                subdomain=service.subdomain,
                route_to=service.project.conf().alb_public_dns,
            )
            for service in self.services.select_related("project").filter(
                is_deleted=False
            )
        ]
        return Route53Configuration(
            domain=self.environment.domain, cname_subdomains=cnames
        )

    def get_alb_conf(self) -> ALBConfigs:
        open_ports = []
        for service in self.services.filter(is_deleted=False):
            open_ports.append(
                OpenPort(
                    name=service.name,
                    container_port=service.container_port,
                    alb_port_http=service.alb_port_http,
                    alb_port_https=service.alb_port_https,
                    health_check_endpoint=service.health_check_endpoint,
                    health_check_protocol=HTTP,
                    ssl_certificate_arn=service.conf().acm_arn,
                )
            )
        return ALBConfigs(alb_name=self.conf().alb_name, open_ports=open_ports)

    def get_ecr_conf(self) -> ECRConfigs:
        repos = []
        for service in self.services.filter(is_deleted=False):
            repos.append(service.conf().ecr_repo_name)

        return ECRConfigs(repositories=repos)

    def get_ssh_key_name(self):
        return f"{self.name}_{self.environment.name}_{self.environment.slug}"

    def get_ssh_key(self):
        with open(
            os.path.join(KEYS_DIR, f"{self.get_ssh_key_name()}.pem"), "rb"
        ) as ssh_key_file:
            ssh_key_content = ssh_key_file.read()
        return ssh_key_content


@dataclass
class ServiceConf:
    acm_arn: str
    health_check_protocol: str
    ecr_repo_name: str
    ecr_repo_url: str = ""
    target_group_arn: str = ""

    def to_str(self):
        return json.dumps(asdict(self))


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

    name = models.CharField(max_length=100, null=False, blank=False)
    subdomain = models.CharField(max_length=50, null=False, blank=False)
    container_port = models.PositiveIntegerField(null=False, blank=False)
    alb_port_http = models.PositiveIntegerField(null=False, blank=False)
    alb_port_https = models.PositiveIntegerField(null=False, blank=False)
    health_check_endpoint = models.CharField(max_length=150, default="/")
    configuration = EncryptedTextField(default="{}")

    last_status = models.ForeignKey(
        ServiceStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="service_object",
    )

    is_deleted = models.BooleanField(default=False)

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
        return f"#{self.id} | Service: {self.service}"


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
        return None

    def mark_result(self, is_success):
        self.is_success = is_success
        self.ended_at = datetime.utcnow().replace(tzinfo=pytz.UTC)
        self.save(update_fields=["is_success", "ended_at"])
