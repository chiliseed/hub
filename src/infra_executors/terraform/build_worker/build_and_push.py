import logging
import os
import subprocess
import sys
import time

FORMAT = (
    "%(asctime)-27s %(name)-22s %(funcName)s %(filename)s %(levelname)s %(message)s"
)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)

logger = logging.getLogger("build-worker")

HERE = os.path.abspath(os.path.dirname(__file__))
REGION = os.environ.get("AWS_DEFAULT_REGION")
ENV = os.environ.get("CHILISEED_ENV")
VERSION = os.environ.get("CHILISEED_VERSION")
DOCKERFILE_TARGET = os.environ.get("DOCKERFILE_TARGET")
SERVICE_NAME = os.environ.get("CHILISEED_SERVICE_NAME")
ECR_URL = os.environ.get("CHILISEED_ECR_URL")
BUILD_VERSION = f"{SERVICE_NAME}:{VERSION}"
REPO = f"{ECR_URL}:{VERSION}"
DEPLOYMENT_ROOT = "/home/ubuntu/deployment/build"


def exec_shell_command(
    cmd,
    env_vars=None,
    cwd=None,
    log_to=None,
):
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


def do_commands(commands):
    """Execute commands one by one and only of previous command succeeded.

    Parameters
    ----------
    commands : iterable(str)
        list of commands to be executed

    Returns
    -------
    None
    """
    start_time = time.time()
    for cmd in commands:
        logger.info(cmd)
        (return_code, stdout) = exec_shell_command(cmd, cwd=DEPLOYMENT_ROOT)
        logger.info("Time elapsed: {}".format(time.time() - start_time))
        if return_code != 0 and stdout:
            return return_code
    return 0


DEPLOYMENT_START = [
    ["docker --version"],
    [f"aws ecr get-login-password | docker login --username AWS --password-stdin {ECR_URL}"],
]

PUSH_IMAGE = [
    [f"docker tag {BUILD_VERSION} {REPO}"],
    [f"docker push {REPO}"]
]

BUILD = [
    [f"docker build -t {BUILD_VERSION} {DEPLOYMENT_ROOT}"]
] + PUSH_IMAGE

BUILD_TO_TARGET = [
    [f"docker build --target {DOCKERFILE_TARGET} -t {BUILD_VERSION} {DEPLOYMENT_ROOT}"]
] + PUSH_IMAGE

if __name__ == "__main__":
    logger.info("Starting build in pwd: %s", HERE)
    logger.info("Deploying version %s for service %s in environment %s", VERSION, SERVICE_NAME, ENV)

    if not os.path.exists(DEPLOYMENT_ROOT):
        logger.error("deployment root not setup")
        exit(1)

    if not os.path.exists(os.path.join(DEPLOYMENT_ROOT, "Dockerfile")):
        logger.error("Deployment dir has no dockerfile")
        exit(1)

    return_code = do_commands(DEPLOYMENT_START)
    if return_code != 0:
        logger.error("Error executing start")
        exit(return_code)

    if DOCKERFILE_TARGET:
        return_code = do_commands(BUILD_TO_TARGET)
        if return_code != 0:
            logger.error("Error executing start")
            exit(return_code)
    else:
        return_code = do_commands(BUILD)
        if return_code != 0:
            logger.error("Error executing start")
            exit(return_code)
