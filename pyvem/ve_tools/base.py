"""
Abstract class for merging the functionality of all the virtual environment
tools in `ve_tools/` to one tool.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from pyvem.pyvem import PyVem


class VirtualEnvironment(ABC, PyVem):
    def __init__(self) -> None:
        super().__init__()
        self.ve_dir = self.pyvem_dir / "ve"
        if not self.ve_dir.exists():
            self.ve_dir.mkdir(parents=True, exist_ok=True)

        self.project_dir = self.ve_dir / self.project_name

    def unlink_ve_dir(self) -> None:
        if not self.project_dir.exists():
            return

        self.project_dir.unlink(missing_ok=True)

    def link_ve_dir(self, link_folder: Path) -> None:
        self.project_dir.symlink_to(link_folder, target_is_directory=True)

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

    @abstractmethod
    def run(self, args: list[str]) -> int:
        """
        Run command in virtual environment.

        Args:
            args: Arguments to be run in virtual environment

        Returns:
            retval
        """
