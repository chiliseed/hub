"""Creates the database inside a vpc."""
import argparse
from typing import NamedTuple, Mapping

from infra_executors.constants import AwsCredentials, GeneralConfiguration
from infra_executors.constructors import build_state_key
from infra_executors.logger import get_logger
from infra_executors.terraform_executor import TerraformExecutor, ExecutorConfiguration

logger = get_logger(__name__)


class DBConfigs(NamedTuple):
    identifier: str
    name: str
    username: str
    password: str

    instance_type: str = "db.t2.large"
    allocated_storage: int = 100


def create_postgresql(
    creds: AwsCredentials, params: GeneralConfiguration, db_conf: DBConfigs
) -> Mapping[str, str]:
    """Create a database."""
    logger.info("Executing run id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=db_conf,
        executor_configs=ExecutorConfiguration(
            name="postgres",
            action="create",
            config_dir="postgres",
            state_key=build_state_key(params, "postgres"),
            variables_file_name="db.tfvars",
        )
    )
    return executor.execute_apply()


def destroy_postgresql(
    creds: AwsCredentials, params: GeneralConfiguration, db_conf: DBConfigs
) -> None:
    """Destroy database."""
    logger.info("Executing destroy postgres. run_id=%s", params.run_id)
    executor = TerraformExecutor(
        creds,
        params,
        cmd_configs=db_conf,
        executor_configs=ExecutorConfiguration(
            name="postgres",
            action="destroy",
            config_dir="postgres",
            state_key=build_state_key(params, "postgres"),
            variables_file_name="db.tfvars",
        )
    )
    executor.execute_destroy()
    logger.info("DB destroyed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create/destroy db in the provides vpc."
    )
    parser.add_argument(
        "cmd",
        type=str,
        default="create",
        help="Sub command. One of: create/destroy",
    )
    parser.add_argument(
        "project_name",
        type=str,
        help="The name of your project. Example: chiliseed",
    )
    parser.add_argument(
        "environment",
        type=str,
        default="develop",
        help="The name of your environment. Example: develop",
    )
    parser.add_argument(
        "vpc_id",
        type=str,
        help="The id of the vpc. Example: vpc-0c5b94e64b709fa24",
    )
    parser.add_argument("--aws-access-key", type=str, dest="aws_access_key")
    parser.add_argument("--aws-secret-key", type=str, dest="aws_secret_key")
    parser.add_argument(
        "--aws-region", type=str, default="us-east-2", dest="aws_region"
    )
    parser.add_argument(
        "--run-id", type=str, default=1, dest="run_id"
    )

    args = parser.parse_args()

    aws_creds = AwsCredentials(
        args.aws_access_key, args.aws_secret_key, "", args.aws_region
    )
    common = GeneralConfiguration(
        args.project_name, args.environment, args.run_id, args.vpc_id
    )
    cmd_configs = DBConfigs(
        identifier="chiliseed-executor-test",
        name="control_center",
        username="chiliseed",
        password="1ZrXivL86bSr",
        allocated_storage=5,
    )

    if args.cmd == "create":
        create_postgresql(aws_creds, common, cmd_configs)
    if args.cmd == "destroy":
        destroy_postgresql(aws_creds, common, cmd_configs)
