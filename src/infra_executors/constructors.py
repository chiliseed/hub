"""Methods that construct objects from input."""
from typing import Mapping, NamedTuple, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from infra_executors.constants import AwsCredentials, GeneralConfiguration


def build_env_vars(
    aws_credentials: "AwsCredentials",
    generic_configs: "GeneralConfiguration",
    cmd_params: Optional[NamedTuple],
) -> Mapping[str, Union[str, int, float]]:
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

    for key, value in enumerate(generic_configs):
        env_vars[f"TF_VAR_{key}"] = value

    if cmd_params:
        for key, value in enumerate(cmd_params):
            env_vars[f"TF_VAR_{key}"] = value

    return env_vars
