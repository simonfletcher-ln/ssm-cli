import argparse
import sys
from confclasses import fields, is_confclass
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
        self._command_subparsers = self.add_subparsers(title="Commands", dest="command", metavar="<command>", parser_class=argparse.ArgumentParser)
        self._command_subparsers_map = {}

        self.add_config_args(config)

    def parse_args(self, args=None):
        # we have to manually do the parents logic here because arguments are added after init
        self._add_container_actions(self.global_args_parser)
        defaults = self.global_args_parser._defaults
        self._defaults.update(defaults)

        if args is None:
            args = sys.argv[1:]
        global_args, unknown = self.global_args_parser.parse_known_args(args, CliNamespace())
        
        args = super().parse_args(unknown, CliNamespace(global_args=global_args))

        if self.help_as_global and global_args.help:
            if args.command and args.command in self._command_subparsers_map:
                self._command_subparsers_map[args.command].print_help()
                self.exit()
            self.print_help()
            self.exit()

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
        parser = self._command_subparsers.add_parser(name, help=help, formatter_class=self.formatter_class, parents=[self.global_args_parser], add_help=not self.help_as_global)
        self._command_subparsers_map[name] = parser
        return parser

    def add_config_args(self, config, prefix=""):
        for field in fields(config):
            if is_confclass(field.type):
                self.add_config_args(field.type, f"{field.name}-")
            else:
                self.global_args_parser.add_argument(f"--{prefix}{field.name.replace('_','-')}", type=field.type, help=field.metadata.get('help', None))



class CliNamespace(argparse.Namespace):
    def update_config(self):
        self._do_update_config(config, vars(self.global_args))
    
    def _do_update_config(self, config, data: dict):
        for field in fields(config):
            name = field.name
            if is_confclass(field.type):
                # If default value in the confclass
                if not hasattr(config, name):
                    raise RuntimeError("Config not loaded before injecting arg overrides")

                prefix = f"{name}_"
                data = {k.replace(prefix, ""): v for k, v in data.items() if k.startswith(prefix)}
                self._do_update_config(getattr(config, name), data)
            elif name in data and data[name] is not None:
                setattr(config, name, data[name])