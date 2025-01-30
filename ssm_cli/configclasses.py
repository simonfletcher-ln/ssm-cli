from argparse import ArgumentParser
from dataclasses import dataclass, fields, field as d_field, MISSING, is_dataclass
from ssm_cli.xdg import get_conf_file
import yaml

import logging
logger = logging.getLogger(__name__)

def configclass(f):
    return dataclass(init=False)(f)

def field(*, default: any = MISSING, help:str = None):
    return d_field(default=default, metadata={'help': help})

class ConfigError(Exception):
    """Custom exception class for configuration errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


# Refactor into methods which use a configclass so it works like dataclass
# eg: 
#   configclasses.load(config) to replace config.load()
class ConfigClass:
    def load(self, args):
        self.from_yaml()
        self.from_args(args)

    def add_arguments(self, parser: ArgumentParser, prefix=""):
        for field in fields(self):
            if isinstance(field.type, type) and issubclass(field.type, ConfigClass):
                field.type().add_arguments(parser, f"{field.name}-")
            else:
                parser.add_argument(f"--{prefix}{field.name.replace('_','-')}", type=field.type, help=field.metadata.get('help', None))

    def from_args(self, args):
        self.from_dict(vars(args)) # we dont like that Namespace here, better to be dict then yaml/args can use the same logic!
    
    def from_dict(self, data: dict):
        for field in fields(self):
            name = field.name
            if is_dataclass(field.type) and issubclass(field.type, ConfigClass):
                if hasattr(self, field.name):
                    value = getattr(self, field.name)
                else:
                    value = field.type()
                if name in data:
                    value.from_dict(data[name])
                else:
                    prefix = f"{name}_"
                    data = {k.replace(prefix, ""): v for k, v in data.items() if k.startswith(prefix)}
                    value.from_dict(data)
                setattr(self, field.name, value)
            elif name in data and data[name] is not None:
                setattr(self, field.name, data[name])
        
    def from_yaml(self):
        path = get_conf_file()
        try:
            with open(path, 'r') as file:
                data = yaml.safe_load(file)
                self.from_dict(data)
        except OSError as e:
            logger.error(f"Failed to open config {path}")
            raise ConfigError(f"Failed to open config {path}") from e
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config {path}")
            raise ConfigError(f"Failed to parse config {path}") from e