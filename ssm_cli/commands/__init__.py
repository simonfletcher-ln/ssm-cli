from typing import Dict
from ssm_cli.commands.base import BaseCommand
from ssm_cli.commands.list import ListCommand
from ssm_cli.commands.shell import ShellCommand
from ssm_cli.commands.proxycommand import ProxyCommandCommand
from ssm_cli.commands.setup import SetupCommand


COMMANDS : Dict[str, BaseCommand] = {
    'list': ListCommand,
    'shell': ShellCommand,
    'proxycommand': ProxyCommandCommand,
    'setup': SetupCommand
}