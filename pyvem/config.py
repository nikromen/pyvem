from os.path import isfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from yaml import safe_load

from pyvem.constants import CONFIG_FILE_LOCATIONS, DEFAULT_PATH_TO_VEM_VENV_FOLDER


# there will be more stuff to check but if not then drop pydantic dependency
class Schema(BaseModel):
    path_to_venv_folder: str


class Config:
    def __init__(self, path_to_venv_folder: Optional[Path] = None) -> None:
        if path_to_venv_folder:
            self.path_to_venv_folder = path_to_venv_folder.expanduser()
        else:
            self.path_to_venv_folder = DEFAULT_PATH_TO_VEM_VENV_FOLDER

    @classmethod
    def _get_config_file_path(cls) -> Optional[Path]:
        for location in CONFIG_FILE_LOCATIONS:
            if isfile(str(location)):
                return location

        return None

    @classmethod
    def get_config(cls) -> "Config":
        cfg_file_path = cls._get_config_file_path()
        if cfg_file_path is None:
            return Config()

        with open(cfg_file_path, "r") as vem_cfg:
            config_dict = safe_load(vem_cfg)

        Schema(**config_dict)
        return Config(**config_dict)
