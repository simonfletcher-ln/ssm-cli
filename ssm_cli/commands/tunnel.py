from ssm_cli.commands.base import BaseCommand
from ssm_cli.instances import Instances, Instance
from ssm_cli.config import config

import logging
logger = logging.getLogger(__name__)

class TunnelCommand(BaseCommand):
    HELP="Tunnel connection via an instance"
    def add_arguments(parser):
        parser.add_argument("group", type=str, help="group to run against")
        parser.add_argument("--remote", type=str, help="remote host to connect to")
        parser.add_argument("--remote-port", type=int, help="remote port to connect to")
        parser.add_argument("--local-port", type=int, help="local port to listen on")


    def run(args, session):
        logger.info("running tunnel action")

        instances = Instances(session)
        instance = instances.select_instance(args.group, config.actions.proxycommand.selector)

        if instance is None:
            logger.error("failed to select host")
            raise RuntimeError("failed to select host")

        logger.info(f"connecting to {repr(instance)}")
        
        instance.start_port_forwarding_session_to_remote_host(session, args.remote, args.remote_port, args.local_port)