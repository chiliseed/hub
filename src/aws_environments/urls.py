"""Url patterns for aws environment package."""
from django.urls import path

from aws_environments.views import (
    EnvironmentCreate,
    EnvironmentList,
    ExecutionLogDetailsView,
    CreateListProject,
    CreateListUpdateServices,
    CreateWorker,
    WorkerDetails,
    DeployService,
    EnvironmentVariables,
)

app_name = "aws_env"
urlpatterns = [
    path("environments/create", EnvironmentCreate.as_view(), name="create_env"),
    path("environments/", EnvironmentList.as_view(), name="list_envs"),
    path(
        "environment/<slug:env_slug>/projects/",
        CreateListProject.as_view({"post": "create", "get": "list"}),
        name="projects",
    ),
    path(
        "project/<slug:project_slug>/services/",
        CreateListUpdateServices.as_view(
            {"post": "create", "get": "list", "patch": "update"}
        ),
        name="services",
    ),
    path(
        "service/<slug:slug>/build", CreateWorker.as_view(), name="launch_build_worker"
    ),
    path("service/<slug:slug>/deploy", DeployService.as_view(), name="deploy_service"),
    path(
        "service/<slug:slug>/environment-variables/",
        EnvironmentVariables.as_view({"get": "list", "post": "create", "delete": "destroy"}),
        name="service_env_vars",
    ),
    path("worker/<slug:slug>", WorkerDetails.as_view(), name="worker"),
    path(
        "execution/status/<slug:slug>",
        ExecutionLogDetailsView.as_view(),
        name="execution_log_details",
    ),
]
