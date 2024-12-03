from pathlib import Path
from typing import Optional

from confz import BaseConfig, EnvSource, FileFormat, FileSource
from pydantic import AnyHttpUrl, SecretStr

_path = Path(__file__).parent / "../config.json"


class AllowedGuildConfig(BaseConfig):
    guild_id: int
    invite: AnyHttpUrl


class Config(BaseConfig):
    name: str
    token: SecretStr
    application_id: int
    channel: int
    prefix: str
    status: str
    id_prefix: str
    allowed_guild: Optional[AllowedGuildConfig] = None

    CONFIG_SOURCES = [
        FileSource(_path, format=FileFormat.JSON, optional=True),
        EnvSource(file=".env", nested_separator="__", prefix="MODMAIL_", allow_all=True),
    ]
