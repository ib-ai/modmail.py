import json
import os
from pathlib import Path

_path = Path(__file__).parent / "../config.json"
_config = json.load(open(_path, 'r'))

token = os.getenv(
    "MODMAIL_TOKEN") if "MODMAIL_TOKEN" in os.environ else _config["token"]
application_id = int(
    os.getenv("MODMAIL_APPLICATION_ID")
) if "MODMAIL_APPLICATION_ID" in os.environ else _config["application_id"]
guild = int(os.getenv(
    "MODMAIL_GUILD")) if "MODMAIL_GUILD" in os.environ else _config["guild"]
channel = int(os.getenv("MODMAIL_CHANNEL")
              ) if "MODMAIL_CHANNEL" in os.environ else _config["channel"]
prefix = os.getenv(
    "MODMAIL_PREFIX") if "MODMAIL_PREFIX" in os.environ else _config["prefix"]
status = os.getenv(
    "MODMAIL_STATUS") if "MODMAIL_STATUS" in os.environ else _config["status"]
id_prefix = os.getenv(
    "MODMAIL_ID_PREFIX"
) if "MODMAIL_ID_PREFIX" in os.environ else _config["id_prefix"]
