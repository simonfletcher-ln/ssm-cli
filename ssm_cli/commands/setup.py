import argparse
import paramiko
from ssm_cli.commands.base import BaseCommand
from ssm_cli.xdg import get_conf_root, get_conf_file, get_log_file, get_ssh_hostkey

import logging
logger = logging.getLogger(__name__)

class SetupCommand(BaseCommand):
    HELP = "Setups up ssm-cli"
    
    def add_arguments(parser):
        parser.add_argument("--replace", action=argparse.BooleanOptionalAction, default=False, help="if we should replace existing")

    def run(args, session):
        logger.info("running setup action")

        create_conf_dir()
        create_conf_file(args.replace)
        create_hostkey()

def create_conf_dir():
    root = get_conf_root(False)
    if root.exists():
        if not root.is_dir():
            raise FileExistsError(f"{root} already exists and is not a directory. Cleanup is likely needed.")
        print(f"{root} - skipping (already exists)")
        return
    
    print(f"{root} - creating directory")
    root.mkdir(511, True, True)

def create_conf_file(replace):
    from confclasses import load_config
    from confclasses_comments import save_config
    from ssm_cli.config import Config

    path = get_conf_file(False)
    if path.exists() and not replace:
        print(f"{path} - skipping (already exists)")
        return
    
    # stop accidental polution of the config object, cannot see 
    # this being a real issue but better to be safe
    config = Config()
    load_config(config, "")

    config.group_tag_key = input(f"What tag to use to split up the instances [{config.group_tag_key}]: ") or config.group_tag_key

    try:
        with path.open("w+") as file:
            save_config(config, file)
            print(f"{path} - created")
    except Exception as e:
        logger.error(e)
        path.unlink(True)

def create_hostkey():
    path = get_ssh_hostkey(False)
    if path.exists():
        print(f"{path} - skipping (already exists)")
        return
    host_key = paramiko.RSAKey.generate(1024)
    host_key.write_private_key_file(path)
    print(f"{path} - created")