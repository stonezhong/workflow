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
    config_file_candidates = [
        os.environ.get("ZWORKFLOW_CONFIG"),
        os.path.join(os.getcwd(), "zworkflow.yaml"),    # 当前目录配置文件
        os.path.expanduser("~/zworkflow.yaml"),         # 用户跟目录的配置文件
    ]

    messages = []
    data = None
    for config_file in config_file_candidates:
        if config_file is None:
            continue
        if os.path.isfile(config_file):
            with open(config_file) as f:
                data = yaml.safe_load(f)
            break
        else:
            messages.append(f"config file {config_file} does not exist")
    
    if data is None:
        raise ValueError(','.join(messages))
    return AppConfig.model_validate(data)

app_config: AppConfig = _load_app_config()
