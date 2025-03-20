from ssm_cli.instances import Instances
from ssm_cli.commands.base import BaseCommand

import logging
logger = logging.getLogger(__name__)

class ListCommand(BaseCommand):
    HELP = """List all instances in a group, if no group provided, will list all available groups"""
    def add_arguments(parser):
        parser.add_argument("group", type=str, nargs="?", help="group to run against")
    
    def run(args, session):
        logger.info("running list action")

        instances = Instances(session)

        if args.group:
            for instance in instances.list_instances(args.group):
                print(instance)
        else:
            for group in instances.list_groups():
                print(group)
