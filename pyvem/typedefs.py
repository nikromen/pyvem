from typing import Callable, Any

from docker import DockerClient
from docker.models.containers import Container as DockerContainer
from docker.models.images import Image as DockerImage
from podman import PodmanClient
from podman.domain.containers import Container as PodmanContainer
from podman.domain.images import Image as PodmanImage


# docker and podman unions
Container = PodmanContainer | DockerContainer
Image = PodmanImage | DockerImage
ContainerClient = PodmanClient | DockerClient

AnyCallable = Callable[..., Any]
