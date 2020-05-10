"""Url patterns for aws environment package."""
from django.urls import path

from aws_environments.views import (
    CreateListProject,
    CreateListUpdateServices,
    CreateWorker,
    DeployService,
    EnvironmentCreate,
    EnvironmentList,
    EnvironmentVariables,
    ExecutionLogDetailsView,
    WorkerDetails,
)
from aws_environments.views.env_vars import ProjectEnvironmentVariables
from aws_environments.views.environment import EnvironmentListServices
from aws_environments.views.resource import (
    CreateDatabaseResource,
    CreateCacheResource,
    CreateStaticsBucket,
    ProjectResources,
    Resources,
)
from aws_environments.views.service import AddDB

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
        "environment/<slug:env_slug>/services/",
        EnvironmentListServices.as_view(),
        name="env_list_services",
    ),
    path(
        "environment/<slug:env_slug>/add-db/",
        CreateDatabaseResource.as_view(),
        name="create_db",
    ),
    path(
        "environment/<slug:env_slug>/add-cache/",
        CreateCacheResource.as_view(),
        name="create_cache",
    ),
    path(
        "project/<slug:project_slug>/services/",
        CreateListUpdateServices.as_view(
            {"post": "create", "get": "list", "patch": "update"}
        ),
        name="services",
    ),
    path(
        "project/<slug:project_slug>/environment-variables/",
        ProjectEnvironmentVariables.as_view(
            {"get": "list", "post": "create", "delete": "destroy"}
        ),
        name="project_env_vars",
    ),
    path(
        "project/<slug:project_slug>/resources/",
        ProjectResources.as_view({"get": "list"}),
        name="project_resources",
    ),
    path(
        "service/<slug:slug>/build", CreateWorker.as_view(), name="launch_build_worker"
    ),
    path("service/<slug:slug>/deploy", DeployService.as_view(), name="deploy_service"),
    path(
        "service/<slug:service_slug>/add-statics-bucket",
        CreateStaticsBucket.as_view(),
        name="add_statics_bucket",
    ),
    path(
        "service/<slug:service_slug>/add-db",
        AddDB.as_view(),
        name="add_db",
    ),
    path(
        "service/<slug:slug>/environment-variables/",
        EnvironmentVariables.as_view(
            {"get": "list", "post": "create", "delete": "destroy"}
        ),
        name="service_env_vars",
    ),
    path("worker/<slug:slug>", WorkerDetails.as_view(), name="worker"),
    path(
        "execution/status/<slug:slug>",
        ExecutionLogDetailsView.as_view(),
        name="execution_log_details",
    ),
    path(
        "resource/<slug:slug>",
        Resources.as_view({"get": "retrieve"}),
        name="resource_details",
    ),
]
