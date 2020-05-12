"""Views for aws environment management."""

from .build_worker import CreateWorker, WorkerDetails
from .deployment import DeployService
from .env_vars import EnvironmentVariables, ProjectEnvironmentVariables
from .environment import EnvironmentCreate, EnvironmentList, EnvironmentListServices
from .execution_log import ExecutionLogDetailsView
from .project import CreateListProject
from .service import CreateListUpdateServices, AddDB
from .resource import (
    CreateDatabaseResource,
    CreateCacheResource,
    CreateStaticsBucket,
    ProjectResources,
    RemoveStaticsBucket,
    Resources,
)
