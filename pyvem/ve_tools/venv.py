import os
import shutil
from os import getcwd, listdir
from pathlib import Path

from pyvem.constants import Shell, REQUIREMENTS_FILE, SUCCESS, INFO_TEMPLATE, VenvEnum
from pyvem.ve_tools.base import PyVem


class Venv(PyVem):
    def __init__(self) -> None:
        super().__init__()
        self.shell = self._get_shell()

    @staticmethod
    def _get_shell() -> Shell:
        shell_path = os.getenv("SHELL")
        if shell_path is None:
            # just try if bash works...
            return Shell.bash

        shell = Path(shell_path).name
        if shell not in Shell.list():
            return Shell.bash

        return Shell[shell]

    def update_deps(self, dev: bool) -> int:
        return self.cmd(self._get_requirements_install_cmd(dev, True)).retval

    def delete(self) -> int:
        shutil.rmtree(self.ve_dir)
        return SUCCESS

    def env_path(self) -> Path:
        return self.ve_dir / "bin" / "python"

    def info(self) -> str:
        py_version = (
            self.cmd([str(self.env_path()), "--version"])
            .stderr_and_stdout.split(" ")[-1]
            .strip()
        )
        return INFO_TEMPLATE.format(
            version=py_version,
            name=self.project_name,
            folder_path=self.ve_dir,
            interpreter_path=self.env_path(),
            venv_type=VenvEnum.venv.value,
        )

    def use(self) -> int:
        activate_suffix = "activate"
        if self.shell != Shell.bash:
            activate_suffix += f".{self.shell.value}"

        activate_script = self.env_path().parent / activate_suffix

        return self.cmd(["source", str(activate_script)], use_venv=True).retval

    def _get_requirements_install_cmd(self, dev: bool, update: bool) -> list[str]:
        cmd = [str(self.env_path()), "-m"]
        if REQUIREMENTS_FILE in listdir(getcwd()):
            base_pip_cmd = "pip install "
            if update:
                base_pip_cmd += "--upgrade"

            cmd.append(f"{base_pip_cmd} -r {REQUIREMENTS_FILE}")
            return cmd

        cmd += ["pip", "install"]
        if update:
            cmd.append("--upgrade")

        cmd.append("-e")

        if dev:
            cmd.append(".[dev]")
        else:
            cmd.append(".")

        return cmd

    def install(self, dev: bool) -> int:
        self.ve_dir.mkdir(parents=True, exist_ok=True)

        commands = [
            ["python", "-m", "venv", str(self.ve_dir)],
            self._get_requirements_install_cmd(dev, False),
        ]
        for command in commands:
            print(" ".join(command))
            retval = self.cmd(command).retval
            if retval != SUCCESS:
                return retval

        return SUCCESS
