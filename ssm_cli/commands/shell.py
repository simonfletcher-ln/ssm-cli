from ssm_cli.instances import Instances
from ssm_cli.config import config
from ssm_cli.commands.base import BaseCommand
from dataclasses import dataclass

import logging
logger = logging.getLogger(__name__)

@dataclass
class ShellConfig:
    selector: str = "tui"

class ShellCommand(BaseCommand):
    CONFIG = ShellConfig
    HELP = "Connects to instances"
    
    def add_arguments(parser):
        parser.add_argument("group", type=str, help="group to run against")

    def run(args, session):
        logger.info("running shell action")

        instances = Instances(session)
        instance = instances.select_instance(args.group, "tui")

        if instance is None:
            logger.error("failed to select host")
            raise RuntimeError("failed to select host")

        logger.info(f"connecting to {repr(instance)}")
        
        instance.start_session(session)