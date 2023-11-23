from os import getcwd
from pathlib import Path
from typing import Optional

from pyvem.constants import NO_DEPS_FOUND, SUCCESS
from pyvem.containers.base import LinuxDistro
from pyvem.containers.handler import ContainerHandler
from pyvem.exceptions import PyVemContainerException
from pyvem.spells import find_first_occurrence_of_file


class RPM(LinuxDistro):
    def __init__(self, repository_name: Optional[str] = None) -> None:
        super().__init__(repository_name)

    @staticmethod
    def get_recipe_path() -> Optional[Path]:
        return find_first_occurrence_of_file(Path(getcwd()), "*.spec")

    @staticmethod
    def _get_deps_from_spec(spec: Path, imaginator: ContainerHandler) -> list[str]:
        retval, output = imaginator.command(
            ["dnf", "install", "'dnf-command(builddep)'", "-y"],
            commit=False,
            raise_on_fail=False,
        )
        if retval != SUCCESS:
            raise PyVemContainerException(NO_DEPS_FOUND.format(code=retval))

        _, output = imaginator.command(
            ["dnf", "builddep", spec, "--assumeno"], commit=False
        )
        out_lines = output.split()
        deps_lines = out_lines[
            out_lines.index("Installing:") + 1 : out_lines.index("Transaction Summary")
        ]
        return list(map(lambda line: line.split()[0], deps_lines))

    def _get_deps(
        self, package: Optional[str], spec: Optional[Path], imaginator: ContainerHandler
    ) -> list[str]:
        if not package:
            if spec is None:
                raise PyVemContainerException(
                    "Please provide some information for installation"
                )

            return self._get_deps_from_spec(spec, imaginator)

        retval, output = imaginator.command(
            ["dnf", "repoquery", "--requires", "--resolve", "--recursive", package],
            commit=False,
            print_logs=False,
            raise_on_fail=False,
        )
        if retval != SUCCESS:
            raise PyVemContainerException(NO_DEPS_FOUND.format(code=retval))

        return [line.strip() for line in output.split("\n")]

    def install(
        self,
        dependencies: Optional[list[str]],
        package: Optional[str],
        recipe: Optional[Path],
        image: str,
    ) -> int:
        self.imaginator.tag(image)
        project_dependencies = dependencies or [] + self._get_deps(
            package, recipe, self.imaginator
        )

        retval, _ = self.imaginator.command(
            ["dnf", "install", project_dependencies, "-y"]
        )
        return retval

    def update(self, packages: Optional[list[str]]) -> int:
        if packages:
            cmd = ["dnf", "upgrade"] + packages + ["-y"]
        else:
            cmd = "dnf upgrade -y"

        retval, _ = self.imaginator.command(cmd)
        return retval


RPM(True, "fedora:latest").install(
    None, None, Path("../../pyvem.spec").resolve(), "sdop"
)
