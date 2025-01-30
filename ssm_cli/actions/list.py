from ssm_cli.context import Context
from ssm_cli.aws import list_groups, list_instances
from ssm_cli.cli import ctx

import logging
logger = logging.getLogger(__name__)


def setup(subparsers, parent_parser):
    list_parser = subparsers.add_parser("list", help="List all instances in a group, if no group provided, will list all available groups", parents=[parent_parser])
    list_parser.set_defaults(action_func=cli)
    list_parser.add_argument("group", type=str, nargs="?", help="group to run against")
    return list_parser

def cli():
    logger.info("running list module")

    if ctx.args.group:
        for instance in list_instances(ctx.args.group):
            print(instance)
    else:
        for group in list_groups():
            print(group)