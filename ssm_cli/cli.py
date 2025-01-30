import argparse
import pkgutil
import sys

import boto3
import botocore
from rich_argparse import ArgumentDefaultsRichHelpFormatter

import ssm_cli.actions
from ssm_cli.context import Context
from ssm_cli.config import Config
from ssm_cli.xdg import get_log_file

import logging
logging.basicConfig(
    level=logging.WARNING,
    filename=get_log_file(),
    filemode='+wt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
ctx = Context()

def cli(argv: list = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Getting everything ready for config has useful logs, this helps develop that area
    for i, arg in enumerate(argv):
        if arg == '--log-level':
            logging.getLogger().setLevel(argv[i+1].upper())
        if arg.startswith('--log-level='):
            logging.getLogger().setLevel(arg.split('=')[1].upper())

    logger.debug(f"CLI called with {argv}")

    # Seperate out the parent parser so that we can add it to the subparsers, stops arguments having to passed in a strange order
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--version", action="version", version="0.1.0") #TODO: swap to pull dynamically
    parent_parser.add_argument("--profile", type=str, help="Which AWS profile to use")

    # Load config object now, so we can add the arguments
    config = Config()
    config.add_arguments(parent_parser.add_argument_group("Config", "Arguments to override config"))

    # Build the actual parser
    parser = argparse.ArgumentParser(
        prog="ssm",
        description="tool to manage AWS SSM",
        parents=[parent_parser],
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )

    # Loop each action and add their subcommands
    action_subparsers = parser.add_subparsers(title="Actions", dest="action", required=True, metavar="<action>")
    for _, module_name, _ in pkgutil.iter_modules(ssm_cli.actions.__path__):
        action_parser = __import__(f"ssm_cli.actions.{module_name}", fromlist="setup").setup(action_subparsers, parent_parser)
        action_parser.formatter_class = ArgumentDefaultsRichHelpFormatter

    args = parser.parse_args(argv)

    # Hide internals from logs
    func = args.action_func
    delattr(args, 'action_func')
    logger.debug(f"Arguments: {args}")

    config.load(args)
    logging.getLogger().setLevel(config.log.level.upper())
    
    for logger_name, level in config.log.loggers.items():
        logger.debug(f"setting logger {logger_name} to {level}")
        logging.getLogger(logger_name).setLevel(level.upper())

    ctx.args = args
    ctx.config = config
    try:
        ctx.session = boto3.Session(profile_name=args.profile)
        if ctx.session.region_name is None:
            eprint(f"AWS config missing region for profile {ctx.session.profile_name}")
            logger.error(f"AWS config missing region for profile {ctx.session.profile_name}")
            return 2
    except botocore.exceptions.ProfileNotFound as e:
        eprint(f"AWS profile invalid")
        logger.error(f"AWS profile invalid: {e}")
        return 2

    try:
        func()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ExpiredTokenException':
            eprint(f"AWS credentials expired")
            logger.error(f"AWS credentials expired")
            return 2
    
    return 0

def eprint(*args, **kwargs):
    print(file=sys.stderr, *args, **kwargs)