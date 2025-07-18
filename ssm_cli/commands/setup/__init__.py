import argparse
from ssm_cli.commands.base import BaseCommand
from ssm_cli.xdg import get_conf_file, get_ssh_hostkey
from ssm_cli.commands.setup.definition import SetupDefinitions
from confclasses import load

import logging
logger = logging.getLogger(__name__)

class SetupCommand(BaseCommand):
    HELP = "Setups up ssm-cli"
    
    def add_arguments(parser):
        parser.add_argument("--replace", action=argparse.BooleanOptionalAction, default=False, help="if we should replace existing")
        parser.add_argument("--definitions", type=str, help="Path to the definitions file")

    def run(args, session):
        logger.info("running setup action")

        definitions = SetupDefinitions()
        if args.definitions:
            with open(args.definitions) as f:
                load(definitions, f)
            logger.info(f"Loaded definitions from {args.definitions}")
        else:
            logger.info("Using default definitions")
            load(definitions, "")

        definitions.run()
