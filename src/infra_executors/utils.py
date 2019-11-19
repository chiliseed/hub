import subprocess


def handle_output(output_stream, printout=True):
    for line in output_stream.stdout:
        if printout:
            print(line.decode(), end="")


def execute_shell_command(cmd: list, env_vars: dict = None, cwd=None):
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
        for line in process.stdout:
            print(line.decode(), end="")
        process.poll()
    return process
