from abc import ABC, abstractmethod

from docker.errors import ImageNotFound as DockerImageNotFound
from podman import PodmanClient
from podman.errors import ImageNotFound as PodmanImageNotFound

from pyvem.constants import PODMAN_URI, SUCCESS
from pyvem.exceptions import PyVemContainerException
from pyvem.typedefs import Container, ContainerClient, Image


class _State(ABC):
    @property
    def handler(self) -> "ContainerHandler":
        return self._handler

    @handler.setter
    def handler(self, handler: "ContainerHandler") -> None:
        self._handler = handler

    @abstractmethod
    def get_image(self, repository_name: str, tag_name: str) -> Image:
        ...

    @abstractmethod
    def tag(self, repository: str) -> None:
        ...

    @abstractmethod
    def command(
        self,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        ...

    @staticmethod
    def _do_command_in_container(
        container: Container,
        command: list[str],
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        stdout_lines = []
        for line in container.logs(stream=True):
            stripped = line.decode().strip()
            stdout_lines.append(stripped)
            if print_logs:
                print(stripped)

        retval = container.wait()
        if raise_on_fail and retval != SUCCESS:
            raise PyVemContainerException(
                f"Command {''.join(command)} failed with code: {retval}"
            )

        return retval, "\n".join(stdout_lines)

    def _command_in_container_with_commit_allowed(
        self,
        container: Container,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        retval, output = self._do_command_in_container(
            container, command, print_logs, raise_on_fail
        )
        if commit:
            container.commit(repository=self.handler._repository_name, tag="latest")

        return retval, output


class RepositoryContainerHandlerState(_State):
    def get_image(self, repository_name: str, tag_name: str) -> Image:
        try:
            return self.handler._client.images.get(f"{repository_name}:{tag_name}")
        except (DockerImageNotFound, PodmanImageNotFound) as exc:
            raise PyVemContainerException(
                f"No repository found under name {repository_name}"
            ) from exc

    def tag(self, repository: str) -> None:
        self.handler._image.tag(repository, tag="latest")

    def command(
        self,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        container = self.handler._client.containers.create(
            image=self.handler._image, command=command, detach=True
        )
        container.start()

        retval, output = self._command_in_container_with_commit_allowed(
            container=container,
            command=command,
            commit=commit,
            print_logs=print_logs,
            raise_on_fail=raise_on_fail,
        )

        container.stop()
        container.remove()
        return retval, output


class ContainerHandlerState(_State):
    def get_image(self, repository_name: str, tag_name: str) -> Image:
        # TODO: they have
        raise PyVemContainerException("Container don't have repo or image")

    def tag(self, repository: str) -> None:
        self.handler._image.tag(repository, tag="latest")

    def command(
        self,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        container = self.handler._client.containers.get(self.handler._repository_name)
        retval, output = self._command_in_container_with_commit_allowed(
            container=container,
            command=command,
            commit=commit,
            print_logs=print_logs,
            raise_on_fail=raise_on_fail,
        )
        return retval, output


class ImageContainerHandlerState(_State):
    def get_image(self, repository_name: str, tag_name: str) -> Image:
        # in fact image name
        return self.handler._client.images.pull(repository_name, tag_name)

    def tag(self, repository: str) -> None:
        _tag_name = "latest"
        self.handler._image.tag(repository, tag=_tag_name)

        # pure image was downloaded from the outside world so keeping the
        # image as is, switching to the tagged one
        self.handler._repository_name = repository
        self.handler._tag_name = _tag_name
        # TODO: do I really want to do this under the hood?
        self.handler.set_state(RepositoryContainerHandlerState())
        self.handler._image = self.get_image(repository, _tag_name)

    def command(
        self,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        if commit:
            raise PyVemContainerException("Unable to make commit to pure image.")

        container = self.handler._client.containers.create(
            image=self.handler._image, command=command, detach=True
        )
        container.start()

        retval, output = self._do_command_in_container(
            container=container,
            command=command,
            print_logs=print_logs,
            raise_on_fail=raise_on_fail,
        )

        if container.status == "running":
            container.stop()

        container.remove()
        return retval, output


DEFAULT_STATE = RepositoryContainerHandlerState()
REPOSITORY_STATE = DEFAULT_STATE
IMAGE_STATE = ImageContainerHandlerState()
CONTAINER_STATE = ContainerHandlerState()


class ContainerHandler:
    """
    Manages images/containers/repos for docker or podman.

    Each command is run around an image. Each time new container is created and then
     committed to the same image if not specified without commits. This means each
     command does a change in image linearly.
    """

    def __init__(
        self,
        repository_name: str,
        client: ContainerClient,
        _state: _State = DEFAULT_STATE,
    ) -> None:
        self.set_state(_state)

        self._repository_name = repository_name
        self._tag_name = "latest"
        if ":" in repository_name:
            split_repo_name = repository_name.split(":")
            self._repository_name = split_repo_name[0]
            self._tag_name = split_repo_name[1]

        self._client = client

        self._image = self.get_image(self._repository_name, self._tag_name)

    def set_state(self, state: _State) -> None:
        self._state = state
        self._state.handler = self

    def command(
        self,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        """
        Create new container, run command in it and store the side effects to image.
        """
        return self._state.command(
            command=command,
            commit=commit,
            print_logs=print_logs,
            raise_on_fail=raise_on_fail,
        )

    def tag(self, repository: str) -> None:
        # TODO: implement versioning with tags and store tag history in pyvem venv
        #  directory. It would require some version control logic.
        self._state.tag(repository=repository)

    def get_image(self, repository_name: str, tag_name: str) -> Image:
        return self._state.get_image(repository_name=repository_name, tag_name=tag_name)


la = PodmanClient(base_url=PODMAN_URI.format(uid="4203067"))
i = ContainerHandler("fedora:latest", la, IMAGE_STATE)
i.tag("sakraprace")
i.set_state(REPOSITORY_STATE)
c = i.command(["dnf", "install", "vim", "-y"])
a = 2
