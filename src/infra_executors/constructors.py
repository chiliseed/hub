"""Methods that construct objects from input."""
import json
import logging
from typing import Mapping, NamedTuple, Optional, TYPE_CHECKING, Type


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from common.typing import NamedTupleProtocol
    from infra_executors.constants import AwsCredentials, GeneralConfiguration


def build_env_vars(
    aws_credentials: "AwsCredentials",
    generic_configs: "GeneralConfiguration",
    cmd_params: Optional[Type["NamedTupleProtocol"]],
) -> Mapping[str, str]:
    """Construct environment variables for terraform.

    Parameters
    ----------
    aws_credentials : infra_executors.constants.AwsCredentials
    generic_configs : infra_executors.constants.GeneralConfiguration
        common configs for every terraform execution.
    cmd_params : NamedTuple
        named tuple with command specific params

    Returns
    -------
    env_vars : dict
        dict of env vars required for terraform execution
    """
    env_vars = dict(
        AWS_ACCESS_KEY_ID=aws_credentials.access_key,
        AWS_SECRET_ACCESS_KEY=aws_credentials.secret_key,
        AWS_SESSION_TOKEN=aws_credentials.session_key,
        AWS_DEFAULT_REGION=aws_credentials.region,
    )

    for key, value in generic_configs._asdict().items():
        env_vars[f"TF_VAR_{key}"] = str(value)

    if cmd_params:
        for key, value in cmd_params._asdict().items():
            if isinstance(value, list):
                try:
                    formatted_val = json.dumps([v._asdict() for v in value])
                except AttributeError:
                    # this is not a named tuple
                    formatted_val = json.dumps(value)
            elif isinstance(value, bool):
                formatted_val = json.dumps(value)
            else:
                formatted_val = str(value)

            env_vars[f"TF_VAR_{key}"] = formatted_val

    logger.debug("env vars: %s", env_vars)
    return env_vars


def build_state_key(
    generic_configs: "GeneralConfiguration", component_name: str
) -> str:
    """Construct a state key in a unified way.

    Parameters
    ----------
    generic_configs : infra_executors.constants.GeneralConfiguration
        common configs for every terraform execution.
    component_name : str
        a name of the constructed component. i.e.: network or postgres

    Returns
    -------
    state key : str
        s3 key path where the state will be saved
    """
    return (
        f"{generic_configs.env_slug}/"
        f"{generic_configs.project_name}/"
        f"{generic_configs.env_name}/"
        f"{component_name}.tfstate"
    )
