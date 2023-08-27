import os
import shutil
import venv
from os import getcwd, listdir, get_terminal_size
from pathlib import Path

from pexpect import spawn

from pyvem.constants import (
    ShellEnum,
    REQUIREMENTS_FILE,
    SUCCESS,
    INFO_TEMPLATE,
    VenvEnum,
)
from pyvem.ve_tools.base import PyVem


class Venv(PyVem):
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
        if self.shell != ShellEnum.bash:
            activate_suffix += f".{self.shell.value}"

        activate_script = self.env_path().parent / activate_suffix

        terminal = get_terminal_size()
        child = spawn(
            str(self.shell_path), ["-i"], dimensions=(terminal.lines, terminal.columns)
        )
        child.send(f"source {str(activate_script)}" + os.linesep)
        child.interact()
        child.close()
        return child.exitstatus

    def _get_requirements_install_cmd(self, dev: bool, update: bool) -> list[str]:
        cmd = [str(self.env_path()), "-m"]
        if REQUIREMENTS_FILE in listdir(getcwd()):
            base_pip_cmd = ["pip", "install"]
            if update:
                base_pip_cmd.append("--upgrade")

            cmd += base_pip_cmd + ["-r", REQUIREMENTS_FILE]
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
        venv.create(str(self.ve_dir), with_pip=True)
        return self.cmd(self._get_requirements_install_cmd(dev, False)).retval
