# All XDG path logic here
from pathlib import Path
from xdg_base_dirs import xdg_config_home


def get_conf_root() -> Path:
    root = xdg_config_home() / 'ssm-cli'
    if not root.exists():
        root.mkdir(parents=True)
        with open(root / 'ssm.yaml', 'w+') as f:
            f.write(DEFAULT_CONFIG)
    return root

def get_conf_file() -> Path:
    return get_conf_root() / 'ssm.yaml'
def get_log_file() -> Path:
    return get_conf_root() / 'ssm.log'


DEFAULT_CONFIG = """---

group_tag_key: group

log:
    level: info
    loggers:
        botocore: warn
"""