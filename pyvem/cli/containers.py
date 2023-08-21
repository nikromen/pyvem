import os
from glob import glob
from os import getcwd

import click
from click import ClickException

from pyvem.containers.rpm import RPM
from pyvem.constants import NO_KNOWN_VENV, NOT_IMPLEMENTED


def get_container_instance() -> RPM:
    spec_pattern = os.path.join(getcwd(), "*.spec")
    result = glob(spec_pattern)
    if not result:
        raise ClickException(NO_KNOWN_VENV)

    return RPM()


@click.group()
def container():
    """Command group that prepare containers"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("install")
def install():
    """Install new container with dependencies"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("update")
def update():
    """Update the dependencies in container"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("run")
def run():
    """Start the container and return its name to stdout"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("stop")
def stop():
    """Stops container"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("delete")
def delete():
    """Deletes the container"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("info")
def info():
    """Prints the container name and ID"""
    raise NotImplementedError(NOT_IMPLEMENTED)
