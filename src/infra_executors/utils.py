import logging
import re
import subprocess


logger = logging.getLogger(__name__)


def execute_shell_command(cmd: list, env_vars: dict = None, cwd=None, log_to=None):
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
    """
    with subprocess.Popen(
        cmd,
        shell=True,
        env=env_vars,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ) as process:
        with open(log_to, 'ab') as logfile:
            for line in process.stdout:
                logfile.write(line)
                logger.info(line.decode())
        process.poll()
    return process.returncode


def extract_outputs(logs):
    """Extract terraform outputs as python objects.

    Parameters
    ----------
    logs : str
        popen stdout result

    Returns
    -------
        outputs : dict
            key values of extracted terraform outputs
    """
    output_lines = logs.splitlines()

    for line in reversed(logs):
        if 'Outputs:' in line:
            break
        output_lines.append(line)

    outputs_joined = "".join(reversed(output_lines)).strip()
    # remove all '\n   '
    clean_output1 = re.sub("[\\n]\s+", "", outputs_joined)
    # replace all ',\n]' with ']'
    clean_output2 = re.sub(",[\\n]]", "]", clean_output1)

    outputs = {}
    for clean_line in clean_output2.splitlines():
        key, value = clean_line.split(" = ")
        outputs[key] = value
    return outputs
