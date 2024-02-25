from os import getcwd
from pathlib import Path
from typing import Optional

from pyvem.cmd import Cmd
from pyvem.config import Config


class PyVem:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.get_config()
        self.cwd = Path(getcwd())
        self.project_name = self.cwd.name
        self.cmd = Cmd(self.cwd).run_cmd
