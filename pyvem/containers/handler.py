from abc import ABC, abstractmethod

from docker.errors import ImageNotFound as DockerImageNotFound
from podman.errors import ImageNotFound as PodmanImageNotFound
from tqdm import tqdm

from pyvem.constants import SUCCESS
from pyvem.exceptions import PyVemContainerException
from pyvem.spells import parse_repository_name
from pyvem.typedefs import Container, ContainerClient, Image


class State(ABC):
    @property
    def handler(self) -> "ContainerHandler":
        return self._handler

    @handler.setter
    def handler(self, handler: "ContainerHandler") -> None:
        self._handler = handler

    @abstractmethod
    def _get_image(self, repository_name: str, tag_name: str) -> Image: ...

    @abstractmethod
    def tag(self, repository: str) -> None: ...

    @abstractmethod
    def command(
        self,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]: ...

    @staticmethod
    def _collect_outputs_from_container(
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
                tqdm.write(stripped)

        retval = container.wait()
        if raise_on_fail and retval != SUCCESS:
            raise PyVemContainerException(
                f"Command {''.join(command)} failed with code: {retval}"
            )

        return retval, "\n".join(stdout_lines)

    def _collect_outputs_from_container_and_commit(
        self,
        container: Container,
        command: list[str],
        commit: bool = True,
        print_logs: bool = True,
        raise_on_fail: bool = True,
    ) -> tuple[int, str]:
        retval, output = self._collect_outputs_from_container(
            container, command, print_logs, raise_on_fail
        )
        if commit:
            container.commit(repository=self.handler._repository_name, tag="latest")

        return retval, output


class RepositoryContainerHandlerState(State):
    def _get_image(self, repository_name: str, tag_name: str) -> Image:
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

        retval, output = self._collect_outputs_from_container_and_commit(
            container=container,
            command=command,
            commit=commit,
            print_logs=print_logs,
            raise_on_fail=raise_on_fail,
        )

        if container.status == "running":
            container.stop()

        container.remove()
        return retval, output


class ContainerHandlerState(State):
    def _get_image(self, repository_name: str, tag_name: str) -> Image:
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
        container.exec_run(command)
        retval, output = self._collect_outputs_from_container_and_commit(
            container=container,
            command=command,
            commit=commit,
            print_logs=print_logs,
            raise_on_fail=raise_on_fail,
        )
        return retval, output


class ImageContainerHandlerState(State):
    def _get_image(self, repository_name: str, tag_name: str) -> Image:
        # in fact image name
        return self.handler._client.images.pull(repository_name, tag_name)

    def tag(self, repository: str) -> None:
        _tag_name = "latest"
        self.handler._image.tag(repository, tag=_tag_name)

        # pure image was downloaded from the outside world so keeping the
        # image as is, switching to the tagged one
        self.handler._repository_name = repository
        self.handler._tag_name = _tag_name

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

        retval, output = self._collect_outputs_from_container(
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
        state: State = DEFAULT_STATE,
    ) -> None:
        self._repository_name, self._tag_name = parse_repository_name(repository_name)
        self._client = client
        self.set_state(state)

    def set_state(self, state: State) -> None:
        self._state = state
        self._state.handler = self
        self._image = self._get_image(self._repository_name, self._tag_name)

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

    def _get_image(self, repository_name: str, tag_name: str) -> Image:
        return self._state._get_image(
            repository_name=repository_name, tag_name=tag_name
        )

    def get_handler_for(
        self, repository_name: str, tag_name: str
    ) -> "ContainerHandler":
        state_to_pass = self._state
        if self._state == IMAGE_STATE:
            state_to_pass = REPOSITORY_STATE

        return self.__class__(
            repository_name=f"{repository_name}:{tag_name}",
            client=self._client,
            state=state_to_pass,
        )
