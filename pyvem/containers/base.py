import os
from abc import ABC, abstractmethod
from functools import cached_property
from os import get_terminal_size
from pathlib import Path
from typing import Optional

from docker import DockerClient
from pexpect import spawn
from podman import PodmanClient

from pyvem.cmd import Cmd
from pyvem.config import Config
from pyvem.constants import DOCKER_URI, MANY_IMAGES, PODMAN_URI
from pyvem.containers.handler import ContainerHandler
from pyvem.exceptions import PyVemContainerException
from pyvem.pyvem import PyVem
from pyvem.spells import nested_get, parse_repository_name
from pyvem.typedefs import Image


def get_container_client(use_podman: bool, cwd: Optional[Path] = None):
    if not use_podman:
        return DockerClient(base_url=DOCKER_URI)

    if cwd is None:
        cmd_cls = Cmd()
    else:
        cmd_cls = Cmd(cwd)

    uid = cmd_cls.run_cmd(["id", "-u"], tee_to_stdout=False).stderr_and_stdout
    return PodmanClient(base_url=PODMAN_URI.format(uid=uid))


class LinuxDistro(ABC, PyVem):
    def __init__(self, repository_name: str, config: Optional[Config] = None) -> None:
        super().__init__(config=config)

        self.client = get_container_client(config.use_podman_engine, self.cwd)
        self.repository_name, self.tag_name = parse_repository_name(repository_name)
        self.container_handler = ContainerHandler(repository_name, self.client)

    @staticmethod
    @abstractmethod
    def get_recipe_path() -> Optional[Path]: ...

    @staticmethod
    def _is_in_repository(repository_name: str, image: Image) -> bool:
        return any(repository_name in repo for repo in image.tags)

    @cached_property
    def _repositories(self) -> list[Image]:
        result = []
        for image in self.client.images.list(all=True):
            if self._is_in_repository(self.project_name, image):
                result.append(image)

        return result

    @abstractmethod
    def install(
        self,
        dependencies: Optional[list[str]],
        package: Optional[str],
        recipe: Optional[Path],
    ) -> int: ...

    @abstractmethod
    def update(self, packages: Optional[list[str]]) -> int: ...

    def _try_to_filter_one_from_repositories(
        self, repository_name: str
    ) -> Optional[Image]:
        one = []
        for image in self._repositories:
            if image.tag() == repository_name:
                one.append(image)

        if len(one) == 1:
            return one[0]

        return None

    def _get_image(self, safe: bool = True) -> Optional[Image]:
        if not self._repositories:
            if safe:
                raise PyVemContainerException(
                    "No image repository for this project found"
                )

            return None

        if len(self._repositories) == 1:
            return self._repositories[0]

        if self.repository_name is None:
            one = self._try_to_filter_one_from_repositories(self.project_name)
            if one is None:
                raise PyVemContainerException(MANY_IMAGES)
            return one

        for image in self._repositories:
            if image.name == self.repository_name:
                return image

        if safe:
            raise PyVemContainerException(
                f"No container found with name {self.repository_name}"
            )
        return None

    def execute(self, user: str, container_name: str, command: str) -> str:
        container = self.client.containers.get(container_name)
        result = container.exec_run(cmd=command, user=user)
        return result.output

    def keep_running(self, container_name: Optional[str] = None) -> None:
        image = self._get_image()
        kwargs = {"image": image, "detach": True}
        if container_name is not None:
            kwargs["name"] = container_name

        container = self.client.containers.run(**kwargs)
        print(f"Container ID: {container.id}")

    def stop(self, container_name: str) -> None:
        container = self.client.containers.get(container_name)
        if container.status != "running":
            return

        container.stop()

    def remove(self) -> None:
        image = self._get_image()
        self.client.images.remove(image.id)

    def delete(self) -> None:
        container = self._get_image(safe=False)
        if container is None:
            return

        container.remove()

    def repositories(self) -> list[str]:
        result = []
        for image in self._repositories:
            for repo in image.tags:
                if self.repository_name in repo:
                    result.append(repo)

        return result

    def run(self, command: list[str]) -> None:
        self.container_handler.command(command)

    def enter(self, user: str, container_name: str) -> int:
        if isinstance(self.client, PodmanClient):
            container_cmd = "podman"
        else:
            container_cmd = "docker"

        terminal = get_terminal_size()
        child = spawn(
            os.getenv("SHELL") or "/bin/bash",
            ["-i"],
            dimensions=(terminal.lines, terminal.columns),
        )
        child.send(
            f"{container_cmd} exec -ti --user {user} {container_name} /bin/bash"
            + os.linesep
        )
        child.interact()
        child.close()
        return child.exitstatus

    def info(self) -> str:
        containers = []
        for container in self.client.containers.list():
            image_name = nested_get(container.attrs, "Config", "Image")
            image = self.client.images.get(image_name)
            if self._is_in_repository(self.repository_name, image):
                containers.append(container)

        if not containers:
            return f"No running containers for tag {self.repository_name}"

        result = []
        for container in containers:
            result.append(container.id)

        return "\n".join(result)
