from rich_argparse import ArgumentDefaultsRichHelpFormatter
from ssm_cli.instances import Instances
from ssm_cli.actions.base import BaseAction

import logging
logger = logging.getLogger(__name__)

class ListAction(BaseAction):
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

def setup(subparsers, parent_parser):
    list_parser = subparsers.add_parser("list", help="List all instances in a group, if no group provided, will list all available groups", parents=[parent_parser])
    list_parser.set_defaults(action_func=cli)
    list_parser.add_argument("group", type=str, nargs="?", help="group to run against")
    list_parser.formatter_class = ArgumentDefaultsRichHelpFormatter


def cli():
    logger.info("running list action")

    instances = Instances()

    if ctx.args.group:
        for instance in instances.list_instances(ctx.args.group):
            print(instance)
    else:
        for group in instances.list_groups():
            print(group)