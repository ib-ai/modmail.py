from pathlib import Path
from confz import BaseConfig, EnvSource, FileFormat, FileSource
from pydantic import SecretStr

_path = Path(__file__).parent / "../config.json"


class Config(BaseConfig):
    token: SecretStr
    application_id: int
    channel: int
    prefix: str
    status: str
    id_prefix: str

    CONFIG_SOURCES = [
        FileSource(_path, format=FileFormat.JSON, optional=True),
        EnvSource(prefix="MODMAIL_", allow_all=True),
    ]
