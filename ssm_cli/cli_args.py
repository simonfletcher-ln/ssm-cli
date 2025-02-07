import argparse
import sys
from ssm_cli.config import config

class CliArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, help_as_global=True, **kwargs):
        self.global_args_parser = argparse.ArgumentParser(add_help=False)
        self.global_args_parser_group = self.global_args_parser.add_argument_group("Global Options")
        
        self.help_as_global = help_as_global
        if help_as_global:
            kwargs['add_help'] = False
            # we cannot use help action here because it will just return the global arguments
            self.global_args_parser_group.add_argument('--help', '-h', action="store_true", help="show this help message and exit")

        super().__init__(*args, **kwargs)
        self._command_subparsers = self.add_subparsers(title="Commands", dest="command", required=True, metavar="<command>", parser_class=argparse.ArgumentParser)
        
        config.add_arguments(self.global_args_parser.add_argument_group("Config", "Arguments to override config"))

    def parse_args(self, args=None, namespace=None):
        # we have to manually do the parents logic here because arguments are added after init
        self._add_container_actions(self.global_args_parser)
        defaults = self.global_args_parser._defaults
        self._defaults.update(defaults)

        if args is None:
            args = sys.argv[1:]
        global_args, unknown = self.global_args_parser.parse_known_args(args, namespace)
        
        if self.help_as_global and global_args.help:
            self.print_help()
            self.exit()
        
        args = super().parse_args(unknown, argparse.Namespace(global_args=global_args))

        # Clean up from parents and help
        for arg in vars(global_args):
            if hasattr(args, arg):
                delattr(args, arg)
        if hasattr(global_args, 'help'):
            delattr(global_args, 'help')
        
        return args

    def add_global_argument(self, *args, **kwargs):
        self.global_args_parser_group.add_argument(*args, **kwargs)
    
    def add_command_parser(self, name, help):
        return self._command_subparsers.add_parser(name, help=help, formatter_class=self.formatter_class, parents=[self.global_args_parser], add_help=not self.help_as_global)
