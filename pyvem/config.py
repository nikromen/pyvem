from os.path import isfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, FilePath
from yaml import safe_load

from pyvem.constants import CONFIG_FILE_LOCATIONS, DEFAULT_PATH_TO_PYVEM_DIR


class Images(BaseModel):
    rpm: str = Field(default="fedora:latest", pattern=r"^[^:]+:[^:]+$")


class Config(BaseModel):
    path_to_pyvem_dir: FilePath = DEFAULT_PATH_TO_PYVEM_DIR
    use_podman_engine: bool = False
    images: Images = Images()

    # config for pydantic
    class Config:
        arbitrary_types_allowed = True

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
            return cls()

        with open(cfg_file_path) as vem_cfg:
            config_dict = safe_load(vem_cfg)

        return cls(**config_dict)
