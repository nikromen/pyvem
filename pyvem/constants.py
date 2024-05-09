from enum import Enum
from pathlib import Path

GLOBAL_CFG = Path("/etc/pyvem/pyvem.cfg")
USER_CFG = Path("~/.config/pyvem.cfg").expanduser()
# order is important! user cfg overrides global cfg
CONFIG_FILE_LOCATIONS = [USER_CFG, GLOBAL_CFG]
DEFAULT_PATH_TO_PYVEM_DIR = Path("~/.local/share/pyvem").expanduser()


GREEN = "\033[32m"
BLUE = "\033[34m"
RESET = "\033[0m"

INFO_TEMPLATE = (
    "\033[34m" + "Python:           " + "\033[32m" + "{version}\n" + "\033[0m"
    "\033[34m" + "Venv name         " + "\033[32m" + "{name}\n" + "\033[0m"
    "\033[34m" + "Venv type:        " + "\033[32m" + "{venv_type}\n" + "\033[0m"
    "\033[34m" + "Folder path:      " + "\033[32m" + "{folder_path}\n" + "\033[0m"
    "\033[34m" + "Interpreter path: " + "\033[32m" + "{interpreter_path}" + "\033[0m"
)

REQUIREMENTS_FILE = "requirements.txt"

SUCCESS = 0
FAILURE = 1

PODMAN_URI = "unix:///run/user/{uid}/podman/podman.sock"
DOCKER_URI = "unix://var/run/docker.sock"


# enums


class ShellEnum(str, Enum):
    bash = "bash"
    fish = "fish"
    csh = "csh"

    @staticmethod
    def list() -> list[str]:
        return list(map(lambda shell: shell.value, ShellEnum))


class VenvEnum(str, Enum):
    pipenv = "pipenv"
    poetry = "poetry"
    venv = "venv"


class LinuxEnvEnum(str, Enum):
    rpm = "RPM"


# very long (error) messages

NO_KNOWN_VENV = "No known python virtual environment found in this project."
NOT_IMPLEMENTED = "This feature has to be yet implemented."
MANY_IMAGES = (
    "There are multiple containers associated with this project,"
    " you need to pick specific image."
)
NO_DEPS_FOUND = (
    "Unable to get dependencies for this project from data you provided."
    " Program ended with code: {code}"
)
