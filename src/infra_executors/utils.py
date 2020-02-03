"""Common infra executors utilities."""
import logging
import re
import subprocess  # nosec
from typing import List, Mapping, Optional, Tuple

import boto3  # type: ignore

from infra_executors.constants import AwsCredentials

logger = logging.getLogger(__name__)


def execute_shell_command(
    cmd: List[str],
    env_vars: Optional[Mapping[str, str]],
    cwd: Optional[str],
    log_to: Optional[str],
) -> Tuple[int, str]:
    """Execute provided command within shell.

    Parameters
    ----------
    cmd : list
        a list of command and it's arguments and options.
        Example: ['ls', '-la']
    env_vars : dict
        a dictionary of key=value that will be injected as subprocess
        environment variables
    cwd : str
        current working directory
    log_to : str
        file to which all logs will be written to

    Returns
    -------
    process return code : int
        0 - success
        1 - error
        -N - process was terminated by signal N
    """
    stdout = ""
    with subprocess.Popen(
        cmd,
        shell=True,  # nosec
        env=env_vars,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ) as process:
        if log_to:
            with open(log_to, "ab") as logfile:
                for line in process.stdout:
                    logfile.write(line)
                    logger.info(line.decode())
                    stdout += line.decode()
        else:
            for line in process.stdout:
                logger.info(line.decode())
                stdout += line.decode()

        process.poll()

    return process.returncode, stdout


def extract_outputs(log_file_path: str) -> Mapping[str, str]:
    """Extract terraform outputs as python objects.

    Parameters
    ----------
    log_file_path : str
        path to run log for processing

    Returns
    -------
    outputs : dict
        key values of extracted terraform outputs
    """
    output_lines = []

    with open(log_file_path, "r") as log_file:
        for line in reversed(log_file.readlines()):
            if "Outputs:" in line:
                break
            if not line.strip():
                continue
            output_lines.append(line)
    outputs_joined = "".join(reversed(output_lines)).strip()
    # remove all '\n   '
    clean_output1 = re.sub(r"[\n]\s+", "", outputs_joined)
    # replace all ',\n]' with ']'
    clean_output2 = re.sub(r",[\n]]", "]", clean_output1)
    outputs = {}
    for clean_line in clean_output2.splitlines():
        key, value = clean_line.split("=")
        outputs[key.strip()] = value.strip()
    return outputs


def get_session(region: str) -> boto3.session.Session:
    """Return new thread-safe Session object.

    Each boto3 client/resource should use it to interact with AWS services.

    More info about it:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html#multithreading-multiprocessing

    Parameters
    ----------
    region : str
        name of the aws region. Example: us-east-1

    Returns
    -------
    boto3.session.Session
        boto3.session.Session instance
    """
    session_config = {"region_name": region}

    return boto3.session.Session(**session_config)


def get_boto3_client(service_name: str, aws_creds: AwsCredentials) -> boto3.client:
    """Initialize boto3 for the service.

    Parameters
    ----------
    aws_creds: AwsCredentials
        aws credentials
    service_name: str
        name of the service. Example: ssm, ec2, s3

    Returns
    -------
    boto3.client
    """
    session = get_session(aws_creds.region)
    return session.client(
        service_name,
        aws_access_key_id=aws_creds.access_key,
        aws_secret_access_key=aws_creds.secret_key,
    )
