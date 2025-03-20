# All XDG path logic here
from pathlib import Path
from xdg_base_dirs import xdg_config_home


def get_conf_root(check=True) -> Path:
    root = xdg_config_home() / 'ssm-cli'
    if check and not root.exists():
        from ssm_cli.commands.setup import create_conf_dir
        create_conf_dir()
    return root

def get_conf_file(check=True) -> Path:
    path = get_conf_root(check) / 'ssm.yaml'
    if check and not path.exists():
        raise EnvironmentError(f"{path} missing, run `ssm setup` to create")
    return path

def get_log_file(check=False) -> Path:
    path = get_conf_root(True) / 'ssm.log'
    if check and not path.exists():
        raise EnvironmentError(f"{path} missing, run `ssm setup` to create")
    return path

def get_ssh_hostkey(check=True) -> Path:
    path = get_conf_root(check) / 'hostkey.pem'
    if check and not path.exists():
        raise EnvironmentError(f"{path} missing, run `ssm setup` to create")
    return path
