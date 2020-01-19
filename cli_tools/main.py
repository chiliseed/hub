import os
import subprocess
import time
from typing import Optional, Mapping, Tuple

import click


DOCKER_COMPOSE = "docker-compose"
HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, "..")
DOCKER_FILE = os.path.join(PROJECT_ROOT, "docker-compose.yml")
PROJECT_DOCKER_COMPOSE = f"{DOCKER_COMPOSE}"


def exec_shell_command(
    cmd: str,
    env_vars: Optional[Mapping[str, str]] = None,
    cwd: Optional[str] = None,
    log_to: Optional[str] = None,
) -> Tuple:
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
                    click.echo(line.decode())
                    stdout += line.decode()
        else:
            for line in process.stdout:
                click.echo(line.decode())
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
        click.echo(cmd)
        (return_code, stdout) = exec_shell_command(cmd, cwd=PROJECT_ROOT)
        click.echo("Time elapsed: {}".format(time.time() - start_time))
        if return_code != 0 and stdout:
            return return_code
    return 0


@click.group()
def cli():
    """Command line shortcuts."""


@cli.command()
def start():
    """Startup all project containers."""
    click.echo("Starting up all project containers")
    commands = (
        'docker ps -q --filter "name=chiliseed_api" '
        '| grep -q . && docker stop chiliseed_api '
        '&& docker rm -fv chiliseed_api',
        f'{PROJECT_DOCKER_COMPOSE} build',
        f'{PROJECT_DOCKER_COMPOSE} up -d --remove-orphans',
    )

    do_commands(commands)


@cli.command()
def restart():
    """Restart api container, without build and with recreate container."""
    click.echo('Restarting api')
    do_commands((
        f"{PROJECT_DOCKER_COMPOSE} stop api",
        f'{PROJECT_DOCKER_COMPOSE} up -d --force-recreate api api',
    ))


@cli.command()
def rebuild():
    """Execute api container restart with rebuild."""
    click.echo("Restarting and rebuilding api")
    do_commands((
        f"{PROJECT_DOCKER_COMPOSE} stop api",
        f"{PROJECT_DOCKER_COMPOSE} build api",
        f"{PROJECT_DOCKER_COMPOSE} up -d --force-recreate api",
    ))


@cli.command()
@click.argument("app", required=False)
def migrate(app):
    """Create migration and apply it."""
    if app:
        click.echo(f"Creating new migration for {app}")
        commands = (
            f"{PROJECT_DOCKER_COMPOSE} exec api python manage.py makemigrations {app}",
            f"{PROJECT_DOCKER_COMPOSE} exec api python manage.py migrate {app}"
        )
    else:
        commands = (
            f"{PROJECT_DOCKER_COMPOSE} exec api python manage.py makemigrations",
            f"{PROJECT_DOCKER_COMPOSE} exec api python manage.py migrate",
        )
    do_commands(commands)


@cli.command()
@click.argument('path', required=False)
def test(path):
    """Run pytest.

    Parameters
    ----------
    path : :obj:`str`, optional
        Optional path to a specific tests file and/or specific test

    Returns
    -------
    pytest output
        result of running the tests

    Examples
    --------
    To collect and run all tests:

        $ ./tools.py test

    To run specific test file:

        $ ./tools.py test users/tests/test_models.py

    To run specific test:

        $ ./tools.py test users/tests/test_models.py::UserModelTestCase
    """
    if path:
        do_commands([f"{PROJECT_DOCKER_COMPOSE} exec api pytest {path}"])
    else:
        do_commands([f"{PROJECT_DOCKER_COMPOSE} exec api pytest"])


@cli.command()
@click.argument("path", required=False)
def black(path):
    """Format the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running black on path: {path}")
    return do_commands(
        [f"{PROJECT_DOCKER_COMPOSE} exec api black --line-length 78 {path}"]
    )


@cli.command()
@click.argument("path", required=False)
def flake8(path):
    """Run flake8 linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running flake8 on path: {path}")
    return do_commands([f"{PROJECT_DOCKER_COMPOSE} exec api flake8 {path} --exclude=migrations --min-python-version 3.7.0"])


@cli.command()
@click.argument("path", required=False)
def pydocstyle(path):
    """Run pydocstyle linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running pydocstyle on path: {path}")
    return do_commands(
        [f'{PROJECT_DOCKER_COMPOSE} exec api pydocstyle --convention numpy {path} --match-dir="^(?!migrations).*"']
    )


@cli.command()
@click.argument("path", required=False)
def prospector(path):
    """Run prospector linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running prospector on path: {path}")
    return do_commands([f"{PROJECT_DOCKER_COMPOSE} exec api prospector {path}"])


@cli.command()
@click.argument("path", required=False)
def bandit(path):
    """Run bandit linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running bandit on path: {path}")
    return do_commands([f"{PROJECT_DOCKER_COMPOSE} exec api bandit {path}"])


@cli.command()
@click.argument("path", required=False)
def mypy(path):
    """Run static type checker for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running mypy on path: {path}")
    return do_commands([f"{PROJECT_DOCKER_COMPOSE} exec api mypy {path} --strict"])


@cli.command()
@click.argument("path", required=False)
@click.pass_context
def lint(ctx, path):
    """Execute formatter and all linters inside api docker."""
    if not path:
        path = "/app"

    linter_jobs = (
        black,
        flake8,
        pydocstyle,
        prospector,
        bandit,
        mypy,
    )
    for job in linter_jobs:
        return_code = ctx.invoke(job, path=path)
        if return_code != 0:
            return
