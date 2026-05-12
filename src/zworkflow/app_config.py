from __future__ import annotations
import os
import yaml
from pydantic import BaseModel

class AppConfig(BaseModel):
    database: DatabaseConfig
    logging: dict
    temporal: TemporalConfig

class DatabaseConfig(BaseModel):
    url: str
    connect_args: dict
    create_tables: bool = False

class TemporalConfig(BaseModel):
    host: str
    port: int
    queue_name: str

def _load_app_config() -> AppConfig:
    config_file = os.path.expanduser(os.environ.get("CONFIG", "~/zworkflow.yaml"))
    if not os.path.isfile(config_file):
        raise ValueError(f"config file \"{config_file}\" not found!")
    
    with open(config_file) as f:
        data = yaml.safe_load(f)

    return AppConfig.model_validate(data)

app_config: AppConfig = _load_app_config()
