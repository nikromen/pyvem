"""
Abstract class for merging the functionality of all the virtual environment
tools in `ve_tools/` to one tool.
"""
from abc import ABC, abstractmethod
from os import getcwd
from pathlib import Path

from pyvem.config import Config
from pyvem.cmd import Cmd


class PyVem(ABC):
    def __init__(self) -> None:
        self.cwd = Path(getcwd())
        self.cmd = Cmd(self.cwd).run_cmd
        self.config = Config.get_config()
        self.project_name = Path(getcwd()).name
        self.ve_dir = self.config.path_to_venv_folder / self.project_name

    def ensure_pyvem_ve_dir(self) -> Path:
        if not self.config.path_to_venv_folder.exists():
            self.ve_dir.parent.mkdir(parents=True, exist_ok=True)

        return self.ve_dir

    def unlink_ve_dir(self) -> None:
        if not self.ve_dir.exists():
            return

        self.ve_dir.unlink(missing_ok=True)

    def link_ve_dir(self, link_folder: Path) -> None:
        self.ensure_pyvem_ve_dir().symlink_to(link_folder, target_is_directory=True)

    @abstractmethod
    def update_deps(self, dev: bool) -> int:
        """
        Updates dependencies in virtual environment.

        Args:
            dev: Install also development dependencies

        Returns:
            retval
        """

    @abstractmethod
    def delete(self) -> int:
        """
        Delete virtual environment of project you are in.

        Returns:
            retval
        """

    @abstractmethod
    def env_path(self) -> Path:
        """
        Returns paths to virtual environment binary.

        Returns:
            Path to python virtual environment.
        """

    @abstractmethod
    def info(self) -> str:
        """
        Shows information about current virtual environment.

        Returns:
            String representing info about virtual environment
        """

    @abstractmethod
    def use(self) -> int:
        """
        Use the virtual environment of project you are in.

        Returns:
            retval
        """

    @abstractmethod
    def install(self, dev: bool) -> int:
        """
        Install new virtual environment to a project you are in.

        Args:
            dev: Install also development dependencies

        Returns:
            retval
        """
