from os import getcwd
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from pyvem.config import Config
from pyvem.constants import NO_DEPS_FOUND, SUCCESS
from pyvem.containers.base import LinuxDistro
from pyvem.exceptions import PyVemContainerException
from pyvem.spells import find_first_occurrence_of_file, progress_bar


class RPM(LinuxDistro):
    def __init__(self, repository_name: str, config: Optional[Config] = None) -> None:
        super().__init__(repository_name, config)

    @staticmethod
    def get_recipe_path() -> Optional[Path]:
        return find_first_occurrence_of_file(Path(getcwd()), "*.spec")

    def _get_deps_from_spec(self, spec: Path, bar: tqdm) -> list[str]:
        bar.total = 4
        bar.refresh()
        bar.update(1)
        bar.set_postfix(
            {"Current job": f"Getting dependencies from spec file: {spec.name}"}
        )

        retval, output = self.container_handler.command(
            ["dnf", "install", "'dnf-command(builddep)'", "-y"],
            commit=False,
            raise_on_fail=False,
        )
        if retval != SUCCESS:
            raise PyVemContainerException(NO_DEPS_FOUND.format(code=retval))

        bar.update(1)

        _, output = self.container_handler.command(
            ["dnf", "builddep", spec, "--assumeno"], commit=False
        )
        out_lines = output.split()
        deps_lines = out_lines[
            out_lines.index("Installing:") + 1 : out_lines.index("Transaction Summary")
        ]
        return list(map(lambda line: line.split()[0], deps_lines))

    def _get_deps(
        self, package: Optional[str], spec: Optional[Path], bar: tqdm
    ) -> list[str]:
        if not package:
            if spec is None:
                raise PyVemContainerException(
                    "Please provide some information for installation"
                )

            return self._get_deps_from_spec(spec, bar)

        bar.total = 3
        bar.refresh()
        bar.update(1)
        bar.set_postfix(
            {"Current job": f"Getting dependencies from package: {package}"}
        )

        retval, output = self.container_handler.command(
            ["dnf", "repoquery", "--requires", "--resolve", "--recursive", package],
            commit=False,
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
    ) -> int:
        with progress_bar(desc=f"Installing repo {self.repository_name}") as bar:
            project_dependencies = dependencies or [] + self._get_deps(
                package, recipe, bar
            )

            bar.update(1)
            bar.set_postfix({"Current job": "Installing dependencies"})
            retval, _ = self.container_handler.command(
                ["dnf", "install", " ".join(project_dependencies), "-y"]
            )

        return retval

    def update(self, packages: Optional[list[str]]) -> int:
        if packages:
            cmd = ["dnf", "upgrade"] + packages + ["-y"]
        else:
            cmd = "dnf upgrade -y"

        retval, _ = self.container_handler.command(cmd)
        return retval
