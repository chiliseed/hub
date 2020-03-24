from dataclasses import dataclass
import json
import os

from django.contrib.auth import get_user_model
from django.db import models
from fernet_fields import EncryptedTextField

from aws_environments.constants import InfraStatus
from common.models import BaseModel
from infra_executors.alb import ALBConfigs, OpenPort, HTTP
from infra_executors.constants import GeneralConfiguration, KEYS_DIR
from infra_executors.ecr import ECRConfigs
from infra_executors.route53 import Route53Configuration, CnameSubDomain

from .environment import Environment
from .utils import BaseConf

User = get_user_model()


@dataclass
class ProjectConf(BaseConf):
    alb_name: str
    alb_public_dns: str
    ecs_cluster: str
    ecs_executor_role_arn: str = ""


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
        return f"Project #{self.project.id} | Status {self.status}"


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
