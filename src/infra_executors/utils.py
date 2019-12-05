"""Common infra executors utilities."""
import logging
import re
import subprocess  # nosec
from typing import List, Mapping, Optional

logger = logging.getLogger(__name__)


def execute_shell_command(
    cmd: List[str],
    env_vars: Optional[Mapping[str, str]],
    cwd: Optional[str],
    log_to: Optional[str],
) -> int:
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
        else:
            for line in process.stdout:
                logger.info(line.decode())
        process.poll()
    return process.returncode


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
        key, value = clean_line.split(" = ")
        outputs[key] = value
    return outputs
