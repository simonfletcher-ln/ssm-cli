from ssm_cli.actions.list import ListAction
from ssm_cli.actions.shell import ShellAction
from ssm_cli.actions.proxycommand import ProxyCommandAction

ACTIONS = {
    'list': ListAction,
    'shell': ShellAction,
    'proxycommand': ProxyCommandAction
}