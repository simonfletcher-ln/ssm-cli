from typing import Dict
from confclasses import confclass

@confclass
class ProxyCommandConfig:
    selector: str = "first"

@confclass
class ActionsConfig:
    proxycommand: ProxyCommandConfig
    
@confclass
class LoggingConfig:
    level: str = "info"
    loggers: Dict[str, str] = {
        "botocore": "warn"
    }
    """key value dictionary to override log level on, some modules make a lot of noise, botocore for example"""

@confclass
class GuiConfig:
    size: str = "800x400"
    title: str = "SSM: Select Host"
    tree_columns:Dict[str,int] = {
        "id": 130,
        "name": 350,
        "ip": 120,
        "ping": 80
    }
    offline_background: str = "lightgrey"

@confclass
class Config:
    log: LoggingConfig
    actions: ActionsConfig
    gui: GuiConfig
    group_tag_key: str = "group"
    """Tag key to use when filtering, this is usually set during ssm setup."""

    
config = Config()
