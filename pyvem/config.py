from os.path import isfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, constr, validator
from yaml import safe_load

from pyvem.constants import CONFIG_FILE_LOCATIONS, DEFAULT_PATH_TO_VEM_VENV_FOLDER


class Images(BaseModel):
    rpm: constr(regex=r"^[^:]+:[^:]+$")


class Config(BaseModel):
    path_to_venv_folder: str | Path
    use_podman_engine: bool
    images: Images

    # config for pydantic
    class Config:
        arbitrary_types_allowed = True

    @validator("path_to_venv_folder")
    def parse_path_to_venv_folder(cls, value: str | Path) -> Path:
        if isinstance(value, str):
            return Path(value).expanduser()

        return value

    @classmethod
    def _get_config_file_path(cls) -> Optional[Path]:
        for location in CONFIG_FILE_LOCATIONS:
            if isfile(str(location)):
                return location

        return None

    @classmethod
    def _construct_default_config(cls) -> "Config":
        images = Images(rpm="fedora:latest")
        config = cls(
            path_to_venv_folder=DEFAULT_PATH_TO_VEM_VENV_FOLDER,
            use_podman_engine=False,
            images=images,
        )
        return config

    @classmethod
    def get_config(cls) -> "Config":
        cfg_file_path = cls._get_config_file_path()
        if cfg_file_path is None:
            return cls._construct_default_config()

        with open(cfg_file_path, "r") as vem_cfg:
            config_dict = safe_load(vem_cfg)

        return cls(**config_dict)
