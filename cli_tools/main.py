import subprocess
import time

import click


def exec_shell_command(cmd):
    """Execute shell command.

    Parameters
    ----------
    cmd : str
        full shell command as a string
    """
    return subprocess.run(cmd, shell=True).returncode


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
        return_code = exec_shell_command(cmd)
        click.echo("Time elapsed: {}".format(time.time() - start_time))
        if return_code != 0:
            return


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
        'docker-compose build',
        'docker-compose up -d --remove-orphans',
    )

    do_commands(commands)


@cli.command()
def restart():
    """Restart api container, without build and with recreate container."""
    click.echo('Restarting api')
    do_commands((
        "docker-compose stop api",
        'docker-compose up -d --force-recreate api api',
    ))


@cli.command()
def rebuild():
    """Execute api container restart with rebuild."""
    click.echo("Restarting and rebuilding api")
    do_commands((
        "docker-compose stop api",
        "docker-compose build api",
        "docker-compose up -d --force-recreate api",
    ))


@cli.command()
@click.argument("app", required=False)
def migrate(app):
    """Create migration and apply it."""
    if app:
        click.echo(f"Creating new migration for {app}")
        commands = (
            "docker-compose exec api python manage.py makemigrations {}".format(app),
            "docker-compose exec api python manage.py migrate {}".format(app)
        )
    else:
        commands = (
            "docker-compose exec api python manage.py makemigrations",
            "docker-compose exec api python manage.py migrate",
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
        exec_shell_command(f"docker-compose exec api pytest {path}")
    else:
        exec_shell_command("docker-compose exec api pytest")


@cli.command()
@click.argument("path", required=False)
def black(path):
    """Format the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running black on path: {path}")
    return exec_shell_command(
        f"docker-compose exec api black --line-length 78 {path}"
    )


@cli.command()
@click.argument("path", required=False)
def flake8(path):
    """Run flake8 linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running flake8 on path: {path}")
    return exec_shell_command(f"docker-compose exec api flake8 {path} --exclude=migrations --min-python-version 3.7.0")


@cli.command()
@click.argument("path", required=False)
def pydocstyle(path):
    """Run pydocstyle linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running pydocstyle on path: {path}")
    return exec_shell_command(
        f'docker-compose exec api pydocstyle --convention numpy {path} --match-dir="^(?!migrations).*"'
    )


@cli.command()
@click.argument("path", required=False)
def prospector(path):
    """Run prospector linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running prospector on path: {path}")
    return exec_shell_command(f"docker-compose exec api prospector {path}")


@cli.command()
@click.argument("path", required=False)
def bandit(path):
    """Run bandit linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running bandit on path: {path}")
    return exec_shell_command(f"docker-compose exec api bandit {path}")


@cli.command()
@click.argument("path", required=False)
def mypy(path):
    """Run static type checker for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running mypy on path: {path}")
    return exec_shell_command(f"docker-compose exec api mypy {path} --strict")


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
