from docker.errors import ImageNotFound as DockerImageNotFound
from podman.errors import ImageNotFound as PodmanImageNotFound
from pyvem.exceptions import PyVemContainerException

from pyvem.constants import SUCCESS

from pyvem.typedefs import ContainerClient, Image


class Imaginator:
    """
    Manages images for docker or podman.

    Each command is run around an image. Each time new container is created and then
     committed to the same image if not specified without commits. This means each
     command does a change in image linearly.
    """

    def __init__(self, tag_name: str, client: ContainerClient) -> None:
        self._tag_name = tag_name
        self._client = client

        self._image = self._client.images.get(tag_name)

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
        container = self._client.containers.create(
            image=self._image, command=command, detach=True
        )
        container.start()

        stdout_lines = []
        for line in container.logs(stream=True):
            stripped = line.strip()
            stdout_lines.append(stripped)
            if print_logs:
                print(stripped)

        retval = container.wait()
        if raise_on_fail and retval != SUCCESS:
            raise PyVemContainerException(
                f"Command {''.join(command)} failed with code: {retval}"
            )

        if commit:
            # no side effects to image
            container.commit(repository=self._tag_name, tag="latest")

        container.stop()
        container.remove()
        return retval, "\n".join(stdout_lines)

    def tag(self, repository: str) -> None:
        self._image.tag(repository, tag="latest")

    @classmethod
    def get_image(cls, image_name: str, client: ContainerClient) -> "Imaginator":
        try:
            client.images.get(image_name)
        except DockerImageNotFound or PodmanImageNotFound:
            client.images.pull(image_name)

        return cls(image_name, client)
