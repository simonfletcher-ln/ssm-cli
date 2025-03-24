import sys

import boto3
import botocore
from rich_argparse import ArgumentDefaultsRichHelpFormatter

from confclasses import load_config
from ssm_cli.config import config
from ssm_cli.xdg import get_log_file, get_conf_file
from ssm_cli.commands import COMMANDS
from ssm_cli.cli_args import CliArgumentParser

import logging
logging.basicConfig(
    level=logging.WARNING,
    filename=get_log_file(),
    filemode='+wt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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

    # Build the actual parser
    parser = CliArgumentParser(
        prog="ssm",
        description="tool to manage AWS SSM",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    parser.add_global_argument("--profile", type=str, help="Which AWS profile to use")

    for name, command in COMMANDS.items():
        command_parser = parser.add_command_parser(name, command.HELP)
        command.add_arguments(command_parser)

    args = parser.parse_args(argv)

    logger.debug(f"Arguments: {args}")

    if not args.command:
        parser.print_help()
        return 1
    
    # Setup is a special case, we cannot load config if we dont have any.
    if args.command == "setup":
        COMMANDS['setup'].run(args, None)
        return 0
    
    try:
        with open(get_conf_file(), 'r') as file:
            load_config(config, file)
            args.update_config()
            logger.debug(f"Config: {config}")
    except EnvironmentError as e:
        eprint(f"Invalid config: {e}")
        return 1
    
    logging.getLogger().setLevel(config.log.level.upper())
    
    for logger_name, level in config.log.loggers.items():
        logger.debug(f"setting logger {logger_name} to {level}")
        logging.getLogger(logger_name).setLevel(level.upper())

    try:
        session = boto3.Session(profile_name=args.global_args.profile)
        if session.region_name is None:
            eprint(f"AWS config missing region for profile {session.profile_name}")
            logger.error(f"AWS config missing region for profile {session.profile_name}")
            return 2
    except botocore.exceptions.ProfileNotFound as e:
        eprint(f"AWS profile invalid")
        logger.error(f"AWS profile invalid: {e}")
        return 2

    try:
        if args.command not in COMMANDS:
            eprint(f"failed to find action {args.action}")
            return 3
        COMMANDS[args.command].run(args, session)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ExpiredTokenException':
            eprint(f"AWS credentials expired")
            logger.error(f"AWS credentials expired")
            return 2
    except Exception as e:
        eprint(e)
        return 5
    
    return 0

def eprint(*args, **kwargs):
    print(file=sys.stderr, *args, **kwargs)