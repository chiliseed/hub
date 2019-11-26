"""Executor for terraform configurations."""
import logging
import os
from typing import List, Mapping, NamedTuple, Optional, TYPE_CHECKING

from infra_executors.constructors import build_env_vars
from infra_executors.utils import execute_shell_command, extract_outputs

if TYPE_CHECKING:
    from infra_executors.constants import (
        AwsCredentials,
        GeneralConfiguration,
        TERRAFORM_DIR,
        EXEC_LOGS_DIR,
        PLANS_DIR,
        TERRAFORM_PLUGIN_DIR,
    )


logger = logging.getLogger(__name__)


class ExecutorConfiguration(NamedTuple):
    """Terraform executor configurations."""

    name: str
    config_dir: str
    variables_file_name: str = ""


class TerraformExecutorError(Exception):
    """Indicates execution error."""


class TerraformExecutor:
    """Generic executor for terraform configurations."""

    config_location: str
    run_log: str
    env_vars: Mapping[str, str]
    plan_file: str
    general_configs: "GeneralConfiguration"
    cmd_configs: Optional[NamedTuple]
    executor_configs: ExecutorConfiguration

    def __init__(
        self,
        creds: "AwsCredentials",
        general_configs: "GeneralConfiguration",
        cmd_configs: Optional[NamedTuple],
        executor_configs: ExecutorConfiguration,
    ):

        self.general_configs = general_configs
        self.cmd_configs = cmd_configs
        self.executor_configs = executor_configs

        self.env_vars = build_env_vars(creds, general_configs, cmd_configs)
        self.config_location = os.path.join(
            TERRAFORM_DIR, executor_configs.config_dir
        )
        self.run_log = os.path.join(
            EXEC_LOGS_DIR, f"network_create_{general_configs.run_id}.log"
        )
        self.plan_file = os.path.join(
            PLANS_DIR,
            f"{executor_configs.name}_{general_configs.run_id}.tfplan",
        )

    @property
    def variables_file(self) -> str:
        return f"{self.executor_configs.variables_file_name}.tfvars"

    @property
    def state_key(self) -> str:
        return f"{self.general_configs.project_name}/{self.executor_configs.name}.tfstate"  # noqa

    def execute_command(self, cmd: List[str]) -> int:
        """Execute terraform shell commands."""
        return execute_shell_command(
            cmd, self.env_vars, self.config_location, self.run_log
        )

    def init_terraform(self) -> None:
        """Initialize terraform state."""
        logger.info("Initializing terraform state")
        init_return_code = self.execute_command(
            [
                f"terraform init "
                f'-backend-config="key={self.state_key}" '
                f"-no-color -reconfigure -plugin-dir {TERRAFORM_PLUGIN_DIR}"
            ]
        )
        if init_return_code != 0:
            logger.error(
                "Failed to init terraform for backend %s",
                self.general_configs.project_name,
            )
            raise TerraformExecutorError("Failed to initialize")

    def prepare_plan(self) -> bool:
        """Run terraform plan."""
        logger.info(
            "Planning terraform changes. run_id=%s",
            self.general_configs.run_id,
        )
        plan_return_code = self.execute_command(
            [
                f"terraform plan "
                f"-detailed-exitcode "
                f"-no-color "
                f"-var-file={self.variables_file} "
                f"-out={self.plan_file}",
            ]
        )

        if plan_return_code == 0:
            logger.info("No changes to apply")
            return False

        if plan_return_code == 1 or plan_return_code < 0:
            logger.error("Error executing %s plan", self.executor_configs.name)
            return False
        return True

    def apply_plan(self) -> Mapping[str, str]:
        """Apply the plan."""
        logger.info("Got changes to apply")
        apply_return_code = self.execute_command(
            [f"terraform apply -auto-approve -no-color {self.plan_file}"]
        )
        if apply_return_code != 0:
            logger.error("Failed to apply a plan %s", self.plan_file)
            return {}

        logger.info("Successfully applied a plan. run_id=%s", self.general_configs.run_id)
        return extract_outputs(self.run_log)

    def execute_apply(self) -> Mapping[str, str]:
        """Run terraform execution."""
        try:
            self.init_terraform()
            has_changes = self.prepare_plan()
            if has_changes:
                return self.apply_plan()
        except TerraformExecutorError:
            logger.error("failed to execute terraform configs")
        return {}

    def execute_destroy(self) -> None:
        """Run terraform destroy."""
        try:
            self.init_terraform()
            self.execute_command([
                f"terraform destroy "
                f"-auto-approve "
                f"-no-color "
                f"-var-file={self.variables_file}"
            ])
        except TerraformExecutorError:
            logger.error("Failed to destroy infrastructure")
