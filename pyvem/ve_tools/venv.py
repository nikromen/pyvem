import os
import shutil
import venv
from os import get_terminal_size, getcwd, listdir
from pathlib import Path

from pexpect import spawn

from pyvem.constants import (
    INFO_TEMPLATE,
    REQUIREMENTS_FILE,
    SUCCESS,
    ShellEnum,
    VenvEnum,
)
from pyvem.ve_tools.base import VirtualEnvironment


class Venv(VirtualEnvironment):
    def __init__(self) -> None:
        super().__init__()
        _shell_path = os.getenv("SHELL") or "/bin/bash"
        self.shell_path = Path(_shell_path)

        self.shell = self._get_shell()

    def _get_shell(self) -> ShellEnum:
        shell = self.shell_path.name
        if shell not in ShellEnum.list():
            return ShellEnum.bash

        return ShellEnum[shell]

    def update_deps(self, dev: bool) -> int:
        return self.cmd(self._get_requirements_install_cmd(dev, True)).retval

    def delete(self) -> int:
        shutil.rmtree(self.project_dir)
        return SUCCESS

    def env_path(self) -> Path:
        return self.project_dir / "bin" / "python3"

    def info(self) -> str:
        py_version = (
            self.cmd([str(self.env_path()), "--version"])
            .stderr_and_stdout.split(" ")[-1]
            .strip()
        )
        return INFO_TEMPLATE.format(
            version=py_version,
            name=self.project_name,
            folder_path=self.project_dir if self.project_dir.exists() else "NA",
            interpreter_path=self.env_path(),
            venv_type=VenvEnum.venv.value,
        )

    def _get_activate_script(self) -> Path:
        activate_suffix = "activate"
        if self.shell != ShellEnum.bash:
            activate_suffix += f".{self.shell.value}"

        return self.env_path().parent / activate_suffix

    def use(self) -> int:
        activate_script = self._get_activate_script()

        terminal = get_terminal_size()
        child = spawn(
            str(self.shell_path), ["-i"], dimensions=(terminal.lines, terminal.columns)
        )
        child.send(f"source {str(activate_script)}" + os.linesep)
        child.interact()
        child.close()
        return child.exitstatus

    def _get_requirements_install_cmd(self, dev: bool, update: bool) -> list[str]:
        cmd = [str(self.env_path()), "-m", "pip", "install"]
        if update:
            cmd.append("--upgrade")

        if REQUIREMENTS_FILE in listdir(getcwd()):
            cmd += ["-r", REQUIREMENTS_FILE]
            return cmd

        cmd.append("-e")
        if dev:
            cmd.append(".[dev]")
        else:
            cmd.append(".")

        return cmd

    def install(self, dev: bool) -> int:
        self.project_dir.mkdir(parents=True, exist_ok=True)
        venv.create(str(self.project_dir), with_pip=True)
        return self.cmd(self._get_requirements_install_cmd(dev, False)).retval

    def run(self, args: list[str]) -> int:
        activate_script = self._get_activate_script()
        activate_cmd = f"source {str(activate_script)} && {' '.join(args)}; deactivate"
        return self.cmd(["bash", "-c", activate_cmd]).retval
