"""Url patterns for aws environment package."""
from django.urls import path

from aws_environments.views import EnvironmentCreate, EnvironmentList, ExecutionLogDetailsView

app_name = "aws_env"
urlpatterns = [
    path("environments/create", EnvironmentCreate.as_view(), name="create_env"),
    path("environments/", EnvironmentList.as_view(), name="list_envs"),
    # path("environment/<slug:slug>/projects/", EnvironmentList.as_view(), name="list_envs"),
    path("execution/status/<slug:slug>", ExecutionLogDetailsView.as_view(), name="execution_log_details"),
]
