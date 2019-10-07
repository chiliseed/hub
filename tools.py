#!.venv/bin/python
import subprocess

import click


def exec_shell_command(cmd, check=True):
    """Execute shell command.

    Parameters
    ----------
    cmd : str
        full shell command as a string
    check : bool, defaults to True
        whether subprocess should check for error codes
    """
    subprocess.run(cmd, shell=True, check=check)


@click.group()
def cli():
    """Command line shortcuts."""


@cli.command()
def start():
    """Startup all project containers."""
    click.echo("Starting up all container")
    exec_shell_command(
        'docker ps -q --filter "name=chiliseed_api" '
        '| grep -q . && docker stop chiliseed_api '
        '&& docker rm -fv chiliseed_api',
        check=False
    )
    exec_shell_command('docker-compose build')
    exec_shell_command('docker-compose up -d --remove-orphans')


@cli.command()
def restart():
    """Restart api container, without build and with recreate container."""
    click.echo('Restarting api')
    exec_shell_command("docker-compose stop api")
    exec_shell_command('docker-compose up -d --force-recreate api api')


@cli.command()
def rebuild():
    """Execute api container restart with rebuild."""
    click.echo("Restarting and rebuilding api")
    exec_shell_command("docker-compose stop api")
    exec_shell_command("docker-compose build api")
    exec_shell_command("docker-compose up -d --force-recreate api")


@cli.command()
@click.argument("app", required=False)
def migrate(app):
    """Create migration and apply it."""
    if app:
        click.echo(f"Creating new migration for {app}")
        exec_shell_command("docker-compose exec api python manage.py makemigrations")


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
    exec_shell_command(
        f"docker-compose exec api black --line-length 78 {path}"
    )


@cli.command()
@click.argument("path", required=False)
def flake8(path):
    """Run flake8 linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running flake8 on path: {path}")
    exec_shell_command(f"docker-compose exec api flake8 {path}")


@cli.command()
@click.argument("path", required=False)
def pydocstyle(path):
    """Run pydocstyle linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running pydocstyle on path: {path}")
    exec_shell_command(
        f"docker-compose exec api pydocstyle --convention numpy {path}"
    )


@cli.command()
@click.argument("path", required=False)
def prospector(path):
    """Run prospector linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running prospector on path: {path}")
    exec_shell_command(f"docker-compose exec api prospector {path}")


@cli.command()
@click.argument("path", required=False)
def bandit(path):
    """Run bandit linter for the code in path."""
    if not path:
        path = "/app"
    click.echo(f"Running bandit on path: {path}")
    exec_shell_command(f"docker-compose exec api bandit {path}")


@cli.command()
@click.argument("path", required=False)
@click.pass_context
def lint(ctx, path):
    """Execute formatter and all linters inside api docker."""
    if not path:
        path = "/app"

    ctx.invoke(black, path=path)
    ctx.invoke(flake8, path=path)
    ctx.invoke(pydocstyle, path=path)
    ctx.invoke(prospector, path=path)
    ctx.invoke(bandit, path=path)


if __name__ == "__main__":
    cli()
