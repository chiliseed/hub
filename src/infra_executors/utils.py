import logging
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
        subprocess.CompletedProcess
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
    return process
