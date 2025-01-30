from typing import Dict
from ssm_cli.configclasses import ConfigClass, configclass, field

@configclass
class LoggingConfig(ConfigClass):
    level: str = field(default="info", help="logging level")
    loggers: Dict[str, str] = field(help="key value dictionary to override log level on")

@configclass
class Config(ConfigClass):
    group_tag_key: str = field(default="group", help="Tag key to use when filtering")
    log: LoggingConfig
    