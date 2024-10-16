import sys
from pathlib import Path

from pyvem.constants import INFO_TEMPLATE, SUCCESS, VenvEnum
from pyvem.exceptions import PyVemException
from pyvem.ve_tools.base import VirtualEnvironment


class Pipenv(VirtualEnvironment):
    def __init__(self) -> None:
        super().__init__()

    def update_deps(self, dev: bool) -> int:
        cmd = ["pipenv", "update"]
        if dev:
            cmd.append("--dev")

        return self.cmd(cmd).retval

    def delete(self) -> int:
        self.unlink_ve_dir()
        return self.cmd(["pipenv", "--rm"]).retval

    def env_path(self) -> Path:
        return Path(
            self.cmd(
                ["pipenv", "--py"], tee_to_stdout=False, raise_on_failure=True
            ).stderr_and_stdout.split("\n")[-1]
        )

    def _get_python_version(self) -> str:
        return self.cmd(
            ["pipenv", "run", "python3", "-V"],
            tee_to_stdout=False,
            raise_on_failure=True,
        ).stderr_and_stdout.split("\n")[-1]

    def info(self) -> str:
        try:
            py_version = self._get_python_version()
        except PyVemException as e:
            if "pipenv --python path/to/python" not in str(e):
                raise

            self.cmd(["pipenv", "--python", sys.executable], raise_on_failure=True)
            py_version = self._get_python_version()

        return INFO_TEMPLATE.format(
            version=py_version,
            name=self.project_name,
            folder_path=self.project_dir if self.project_dir.exists() else "NA",
            interpreter_path=str(self.env_path()),
            venv_type=VenvEnum.pipenv.value,
        )

    def use(self) -> int:
        return self.cmd(["pipenv", "shell"], use_venv=True).retval

    def install(self, dev: bool) -> int:
        retval = self.cmd(["pipenv", "--python", sys.executable]).retval
        if retval != 0:
            return retval

        cmd = ["pipenv", "install"]
        if dev:
            cmd.append("--dev")

        retval = self.cmd(cmd).retval
        if retval == SUCCESS:
            self.link_ve_dir(self.env_path().parent.parent)

        return retval

    def run(self, args: list[str]) -> int:
        return self.cmd(["pipenv", "run"] + args).retval
