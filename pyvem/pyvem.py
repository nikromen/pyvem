from os import getcwd
from pathlib import Path

from pyvem.cmd import Cmd
from pyvem.config import Config


class PyVem:
    def __init__(self) -> None:
        self.config = Config.get_config()
        self.cwd = Path(getcwd())
        self.project_name = self.cwd.name
        self.cmd = Cmd(self.cwd).run_cmd
