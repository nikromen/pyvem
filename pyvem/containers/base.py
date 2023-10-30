import os
from abc import ABC, abstractmethod
from functools import cached_property
from os import get_terminal_size
from pathlib import Path
from typing import Optional

from docker import DockerClient
from pexpect import spawn
from podman import PodmanClient

from pyvem.constants import DOCKER_URI, MANY_IMAGES, PODMAN_URI
from pyvem.containers.handler import Imaginator
from pyvem.exceptions import PyVemContainerException
from pyvem.pyvem import PyVem
from pyvem.spells import nested_get
from pyvem.typedefs import Image


class LinuxDistro(ABC, PyVem):
    def __init__(self, podman: bool, tag_name: Optional[str]) -> None:
        super().__init__()

        if podman:
            self.config.use_podman_engine = True

        if self.config.use_podman_engine:
            uid = self.cmd(["id", "-u"], tee_to_stdout=False).stderr_and_stdout
            self.client = PodmanClient(base_url=PODMAN_URI.format(uid=uid))
        else:
            self.client = DockerClient(base_url=DOCKER_URI)

        self.tag_name = tag_name
        if tag_name is not None:
            self.imaginator = Imaginator(self.project_name, self.client)
        else:
            self.imaginator = None

    @staticmethod
    @abstractmethod
    def get_recipe_path() -> Optional[Path]:
        ...

    @staticmethod
    def _is_in_tags(tag_name: str, image) -> bool:
        return any(tag_name in tag for tag in image.tags)

    @cached_property
    def _images(self) -> list[Image]:
        result = []
        for image in self.client.images.list(all=True):
            if self._is_in_tags(self.project_name, image):
                result.append(image)

        return result

    @abstractmethod
    def install(
        self,
        dependencies: Optional[list[str]],
        package: Optional[str],
        recipe: Optional[Path],
        image: str,
    ) -> int:
        ...

    @abstractmethod
    def update(self, packages: Optional[list[str]]) -> int:
        ...

    def _try_to_filter_one_from_images(self, tag_name: str) -> Optional[Image]:
        one = []
        for image in self._images:
            if image.tag() == tag_name:
                one.append(image)

        if len(one) == 1:
            return one[0]

        return None

    def _get_image(self, safe: bool = True) -> Optional[Image]:
        if not self._images:
            if safe:
                raise PyVemContainerException("No containers for this project found")

            return None

        if len(self._images) == 1:
            return self._images[0]

        if self.tag_name is None:
            one = self._try_to_filter_one_from_images(self.project_name)
            if one is None:
                raise PyVemContainerException(MANY_IMAGES)
            return one

        for image in self._images:
            if image.name == self.tag_name:
                return image

        if safe:
            raise PyVemContainerException(
                f"No container found with name {self.tag_name}"
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

    def images(self) -> list[str]:
        result = []
        for image in self._images:
            for tag in image.tags:
                if self.tag_name in tag:
                    result.append(tag)

        return result

    def run(self, command: list[str]) -> None:
        self.imaginator.command(command)

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
            if self._is_in_tags(self.tag_name, image):
                containers.append(container)

        if not containers:
            return f"No running containers for tag {self.tag_name}"

        result = []
        for container in containers:
            result.append(container.id)
        return "\n".join(result)
