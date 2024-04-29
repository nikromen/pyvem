from os import getcwd, listdir

import click

from pyvem.constants import NO_KNOWN_VENV
from pyvem.exceptions import PyVemException
from pyvem.ve_tools.pipenv import Pipenv
from pyvem.ve_tools.poetry import Poetry
from pyvem.ve_tools.venv import Venv


def get_venv_instance() -> Poetry | Pipenv | Venv:
    dir_content = listdir(getcwd())
    if "Pipfile" in dir_content:
        return Pipenv()

    if (
        "pyproject.toml" in dir_content
        and "[tool.poetry]" in open("pyproject.toml").read()
    ):
        return Poetry()

    if "setup.py" in dir_content or "pyproject.toml" in dir_content:
        return Venv()

    raise PyVemException(NO_KNOWN_VENV)


ins = get_venv_instance


@click.command("delete")
def delete() -> None:
    """Removes virtual environment of the project you are currently in."""
    exit(ins().delete())


@click.command("info")
def info() -> None:
    """Prints information of the project you are currently in."""
    print(ins().info())


@click.command("use")
def use() -> None:
    """Activates the virtual environment of the current project."""
    exit(ins().use())


@click.command("install")
@click.option(
    "-d", "--dev", is_flag=True, default=False, help="Install dev dependencies"
)
def install(dev: bool) -> None:
    """Creates new virtual environment for current project and installs dependencies."""
    exit(ins().install(dev))


@click.command("env-path")
def env_path() -> None:
    """Prints path to virtual environment."""
    print(ins().env_path())


@click.command("update")
@click.option(
    "-d", "--dev", is_flag=True, default=False, help="Install dev dependencies"
)
def update_deps(dev: bool) -> None:
    """Updates dependencies in virtual environment"""
    exit(ins().update_deps(dev))


@click.command("run")
@click.argument("command", type=str)
def run(command: str) -> None:
    """Runs a specified command inside the corresponding virtual environment."""
    exit(ins().run(command.split()))
