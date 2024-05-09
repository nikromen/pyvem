from pathlib import Path

from pyvem.constants import INFO_TEMPLATE, SUCCESS, VenvEnum
from pyvem.exceptions import PyVemException
from pyvem.ve_tools.base import VirtualEnvironment


class Poetry(VirtualEnvironment):
    def __init__(self) -> None:
        super().__init__()

    def update_deps(self, dev: bool) -> int:
        cmd = ["poetry", "update"]
        if not dev:
            cmd += ["--only", "main"]

        return self.cmd(cmd).retval

    def delete(self) -> int:
        self.unlink_ve_dir()
        return self.cmd(["poetry", "env", "remove", "--all"]).retval

    def env_path(self) -> Path:
        output = self.cmd(
            ["poetry", "env", "info"], tee_to_stdout=False, raise_on_failure=True
        )
        for line in output.stderr_and_stdout.split("\n"):
            if line.startswith("Executable:"):
                return Path(line.split(":")[-1].strip())

        raise PyVemException("No executable env path provided by poetry")

    def info(self) -> str:
        output = self.cmd(
            ["poetry", "env", "info"], tee_to_stdout=False, raise_on_failure=True
        )

        py_version = ""
        for line in output.stderr_and_stdout.split("\n"):
            if line.startswith("Python:"):
                py_version = line.split(":")[-1].strip()
                break

        return INFO_TEMPLATE.format(
            version=py_version,
            name=self.project_name,
            folder_path=self.project_dir if self.project_dir.exists() else "NA",
            interpreter_path=str(self.env_path()),
            venv_type=VenvEnum.poetry.value,
        )

    def use(self) -> int:
        return self.cmd(["poetry", "shell"], use_venv=True).retval

    def install(self, dev: bool) -> int:
        cmd = ["poetry", "install"]
        if not dev:
            cmd += ["--only", "main"]

        retval = self.cmd(cmd).retval
        if retval == SUCCESS:
            self.link_ve_dir(self.env_path().parent.parent)

        return retval

    def run(self, args: list[str]) -> int:
        return self.cmd(["poetry", "run"] + args).retval
