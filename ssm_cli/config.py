from typing import Dict
from ssm_cli.configclasses import ConfigClass, configclass, field

@configclass
class ShellConfig(ConfigClass):
    selector: str = field(default="tui", help="which selector to use")

@configclass
class ProxyCommandConfig(ConfigClass):
    selector: str = field(default="first", help="which selector to use")

@configclass
class ActionsConfig(ConfigClass):
    shell: ShellConfig
    proxycommand: ProxyCommandConfig

@configclass
class LoggingConfig(ConfigClass):
    level: str = field(default="info", help="logging level")
    loggers: Dict[str, str] = field(help="key value dictionary to override log level on")

@configclass
class Config(ConfigClass):
    group_tag_key: str = field(default="group", help="Tag key to use when filtering")
    log: LoggingConfig
    actions: ActionsConfig

config = Config()
