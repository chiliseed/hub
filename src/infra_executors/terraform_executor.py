"""Executor for terraform configurations."""
import json
import os
from typing import List, Mapping, NamedTuple, Optional, TYPE_CHECKING, Tuple, Any

from common.crypto import get_uuid_hex

from infra_executors.constants import (
    EXEC_LOGS_DIR,
    PLANS_DIR,
    TERRAFORM_DIR,
    TERRAFORM_PLUGIN_DIR,
)
from infra_executors.constructors import build_env_vars
from infra_executors.logger import get_logger
from infra_executors.utils import execute_shell_command

if TYPE_CHECKING:
    from infra_executors.constants import (
        AwsCredentials,
        GeneralConfiguration,
    )


logger = get_logger(__name__)


class ExecutorConfiguration(NamedTuple):
    """Terraform executor configurations."""

    name: str
    action: str
    config_dir: str
    state_key: str
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
    cmd_configs: Optional[Any]
    executor_configs: ExecutorConfiguration

    def __init__(
        self,
        creds: "AwsCredentials",
        general_configs: "GeneralConfiguration",
        cmd_configs: Optional[Any],
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
            EXEC_LOGS_DIR, f"{executor_configs.name}_{executor_configs.action}_{general_configs.run_id}.log"  # noqa
        )
        self.plan_file = os.path.join(
            PLANS_DIR,
            f"{executor_configs.name}_{general_configs.run_id}_{get_uuid_hex(4)}.tfplan",
        )

    def execute_command(self, cmd: List[str]) -> Tuple[int, str]:
        """Execute terraform shell commands."""
        logger.info("Executing terraform with vars_file=%s", self.executor_configs.variables_file_name)
        return execute_shell_command(
            cmd, self.env_vars, self.config_location, self.run_log
        )

    def init_terraform(self) -> None:
        """Initialize terraform state."""
        logger.info("Initializing terraform state. state_key=%s", self.executor_configs.state_key)
        (init_return_code, _) = self.execute_command(
            [
                f"terraform init "
                f'-backend-config="key={self.executor_configs.state_key}" '
                f"-no-color "
                f"-reconfigure "
                f"-plugin-dir {TERRAFORM_PLUGIN_DIR}"
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
        if self.executor_configs.variables_file_name:
            cmd = [
                    f"terraform plan "
                    f"-detailed-exitcode "
                    f"-no-color "
                    f"-var-file={self.executor_configs.variables_file_name} "
                    f"-out={self.plan_file}",
                ]
        else:
             cmd = [
                    f"terraform plan "
                    f"-detailed-exitcode "
                    f"-no-color "
                    f"-out={self.plan_file}",
                ]

        (plan_return_code, _) = self.execute_command(cmd)

        if plan_return_code == 0:
            logger.info("No changes to apply")
            return False

        if plan_return_code == 1 or plan_return_code < 0:
            logger.error(
                "Error executing %s plan", self.executor_configs.name
            )
            return False
        return True

    def apply_plan(self) -> Any:
        """Apply the plan."""
        logger.info("Got changes to apply")
        (apply_return_code, _) = self.execute_command(
            [f"terraform apply -auto-approve -no-color {self.plan_file}"]
        )
        if apply_return_code != 0:
            logger.error("Failed to apply a plan %s", self.plan_file)
            return {}

        logger.info(
            "Successfully applied a plan. run_id=%s",
            self.general_configs.run_id,
        )

        return self._get_outputs()

    def execute_apply(self) -> Any:
        """Run terraform execution."""
        try:
            self.init_terraform()
            has_changes = self.prepare_plan()
            if has_changes:
                return self.apply_plan()
            return self._get_outputs()
        except TerraformExecutorError:
            logger.error("failed to execute terraform configs")
        return {}

    def get_outputs(self) -> Any:
        """Run init and then get outputs."""
        try:
            self.init_terraform()
            return self._get_outputs()
        except TerraformExecutorError:
            return {}

    def _get_outputs(self) -> Any:
        """Get output for provided terraform configuration."""
        try:
            (get_output, stdout) = self.execute_command([
                f"terraform output -json"
            ])
            if get_output != 0:
                logger.error(
                    "Failed to get terraform output: %s", self.config_location
                )
                return {}
            return json.loads(stdout)
        except TerraformExecutorError:
            logger.error("failed to execute terraform configs")
        return {}

    def execute_destroy(self) -> None:
        """Run terraform destroy."""
        self.init_terraform()
        if self.executor_configs.variables_file_name:
            cmd = [
                f"terraform destroy "
                f"-auto-approve "
                f"-no-color "
                f"-var-file={self.executor_configs.variables_file_name}"
            ]
        else:
            cmd = [
                f"terraform destroy "
                f"-auto-approve "
                f"-no-color "
            ]
        (destroy_response_code, stdout) = self.execute_command(cmd)
        if destroy_response_code != 0:
            raise TerraformExecutorError("Error destroying infrastructure")
