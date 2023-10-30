import os.path
from dataclasses import dataclass
from os import getcwd
from pathlib import Path
from typing import Optional, Type

import click
from click import Context, pass_context

from pyvem.config import Config
from pyvem.constants import NOT_IMPLEMENTED
from pyvem.containers.rpm import RPM

image_tag = click.argument(
    "tag_name",
    type=str,
    required=False,
    default=os.path.basename(getcwd()),
)


def get_container_type() -> Type[RPM]:
    result = list(Path(getcwd()).rglob("**/*.spec"))
    if not result:
        pass
        # in case of more container instances
        # raise ClickException(NO_KNOWN_VENV)

    return RPM


def get_recipe_path_as_text() -> Optional[str]:
    path = get_container_type().get_recipe_path()
    if path is not None:
        return str(path)
    return None


@dataclass
class Obj:
    c_object: Type[RPM]
    podman: bool


@click.group()
@click.option(
    "--podman",
    is_flag=True,
    default=False,
    help="Use podman as container engine instead of docker",
)
@pass_context
def container(ctx: Context, podman: bool) -> None:
    """Command group that prepare images and containers"""
    ctx.obj = Obj(
        c_object=get_container_type(),
        podman=podman,
    )


@container.command("install")
@click.option(
    "-d",
    "--dependency",
    type=str,
    required=False,
    default=None,
    multiple=True,
    help="Specify extra dependencies",
)
@click.option(
    "-p",
    "--package",
    type=str,
    required=False,
    default=None,
    help="From this package the dependencies will be installed",
)
@click.option(
    "-r",
    "--recipe",
    type=click.Path(exists=True),
    required=False,
    default=get_recipe_path_as_text(),
    show_default=True,
    help="Recipe file to obtain dependencies (*.spec, *.pkg, ...)",
)
@click.option(
    "-i",
    "--image",
    type=str,
    required=False,
    default=Config.get_config().images["rpm"],
    show_default=True,
    help="Specific image to pull. e.g. fedora:latest",
)
@click.argument("tag_name", type=str)
@pass_context
def install(
    ctx: Context,
    dependency: Optional[list[str]],
    package: Optional[str],
    recipe: Optional[str],
    image: str,
    tag_name: str,
) -> None:
    """Install new image with dependencies"""
    ctx.obj.c_object(True, tag_name).install(dependency, package, Path(recipe), image)


@container.command("update")
@click.option(
    "-p",
    "--packages",
    type=str,
    required=False,
    default=None,
    multiple=True,
    help="Specify packages to be updated",
)
@image_tag
def update(ctx: Context, packages: Optional[list[str]], tag_name: str) -> None:
    """Update the packages in this image"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("keep-running")
@image_tag
@click.argument(
    "container_name",
    type=str,
    required=False,
    default=None,
)
def keep_running(ctx: Context, tag_name: str, container_name: str):
    """
    Start container with infinitely running command and return its ID to stdout.
    You won't be able to see output from the container tho
    """
    pass


@container.command("run")
@image_tag
@click.argument("command", type=str)
def run(ctx: Context, tag_name: str):
    """Start container associated with tag and run command in it."""
    pass


@container.command("stop")
@click.option(
    "-i",
    "--id",
    type=str,
    required=False,
    default=None,
    multiple=True,
    help="Specify which containers should be stopped",
)
@click.argument(
    "container_name",
    type=str,
    required=False,
    default=os.path.basename(getcwd()),
)
def stop(ctx: Context, id_: str, container_name: str):
    """Stops running container or containers associated with tag name"""
    pass


@container.command("delete")
@image_tag
def remove(ctx: Context, tag_name: str):
    """Remove the image"""
    pass


@container.command("info")
@image_tag
def info(ctx: Context, tag_name: str):
    """Prints the running containers based on given"""
    raise NotImplementedError(NOT_IMPLEMENTED)


c_user = click.option(
    "-u",
    "--user",
    default="root",
    show_default=True,
    help="Enter the container as specific user",
)


@container.command("enter")
@c_user
@click.argument("container_name", type=str)
def enter(ctx: Context, user: str, container_name: str):
    """Enter the container with bash"""
    pass


@container.command("exec")
@c_user
@click.option(
    "--no-commit",
    is_flag=True,
    default=False,
    help="Don't commit effect of command to an image",
)
@click.argument(
    "container_name",
    type=str,
    required=False,
    default=os.path.basename(getcwd()),
)
@click.argument("command", type=str)
def execute(ctx: Context, user: str, container_name: str, command: str):
    """Execute command inside running container"""
    pass


@container.command("images")
@image_tag
def images(ctx: Context):
    """List all image names associated with project according to tag name"""
    pass
