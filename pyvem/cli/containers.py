import os.path
from dataclasses import dataclass
from os import getcwd
from pathlib import Path
from typing import Optional, Type

import click
from click import Context, pass_context

from pyvem.config import Config
from pyvem.constants import NOT_IMPLEMENTED
from pyvem.containers.base import get_container_client
from pyvem.containers.handler import IMAGE_STATE, ContainerHandler
from pyvem.containers.rpm import RPM
from pyvem.spells import find_first_occurrence_of_file, parse_repository_name

repository_name_arg = click.argument(
    "repository_name",
    type=str,
    required=False,
    default=os.path.basename(getcwd()),
)


def get_container_type() -> Type[RPM]:
    result = find_first_occurrence_of_file(Path(getcwd()), "*.spec")
    if result is None:
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
class _Obj:
    c_object: Type[RPM]
    config: Config


@click.group()
@click.option(
    "--podman",
    is_flag=True,
    default=None,
    help="Use podman as container engine instead of docker",
)
@pass_context
def container(ctx: Context, podman: bool) -> None:
    """Command group that prepare images and containers"""
    config = Config.get_config()
    if podman:
        config.use_podman_engine = True

    ctx.obj = _Obj(
        c_object=get_container_type(),
        config=config,
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
    "--image-name",
    type=str,
    required=False,
    default=Config.get_config().images.rpm,
    show_default=True,
    help="Specific image to pull. e.g. fedora:latest",
)
@repository_name_arg
@pass_context
def install(
    ctx: Context,
    dependency: Optional[list[str]],
    package: Optional[str],
    recipe: str,
    image_name: str,
    repository_name: str,
) -> None:
    """Install new image with dependencies"""
    container_client = get_container_client(ctx.obj.config.use_podman_engine)
    container_handler = ContainerHandler(repository_name, container_client, IMAGE_STATE)
    image_name, tag_name = parse_repository_name(image_name)
    repo_container_handler = container_handler.get_handler_for(image_name, tag_name)
    repo_name, _ = parse_repository_name(repository_name)
    repo_container_handler.tag(repo_name)

    ctx.obj.c_object(repository_name=repository_name, config=ctx.obj.config).install(
        dependency, package, Path(recipe)
    )


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
@repository_name_arg
def update(ctx: Context, packages: Optional[list[str]], repository_name: str) -> None:
    """Update the packages in this image repository"""
    raise NotImplementedError(NOT_IMPLEMENTED)


@container.command("keep-running")
@repository_name_arg
@click.argument(
    "container_name",
    type=str,
    required=False,
    default=None,
)
def keep_running(ctx: Context, repository_name: str, container_name: str):
    """
    Start container with infinitely running command and return its ID to stdout.
    You won't be able to see output from the container tho
    """
    pass


@container.command("run")
@repository_name_arg
@click.argument("command", type=str)
def run(ctx: Context, repository_name: str):
    """
    Start container associated with given repository name and run command in it.
    """
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
    """Stops running container or containers associated with repository name"""
    pass


@container.command("delete")
@repository_name_arg
def remove(ctx: Context, repository_name: str):
    """Remove the image in repository matching the given name."""
    pass


@container.command("info")
@repository_name_arg
def info(ctx: Context, repository_name: str):
    """Prints the running containers based on given"""
    raise NotImplementedError(NOT_IMPLEMENTED)


c_user = click.option(
    "-u",
    "--user",
    default="root",
    show_default=True,
    help="Enter the container as specific user (root, ...)",
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
@repository_name_arg
def images(ctx: Context, repository_name: str):
    """List all image names associated with project according to repository name"""
    pass
