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
class Config:
    log: LoggingConfig
    actions: ActionsConfig
    group_tag_key: str = "group"
    """Tag key to use when filtering, this is usually set during ssm setup."""

config = Config()
