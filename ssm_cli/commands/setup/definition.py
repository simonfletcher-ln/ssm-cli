from typing import List
from confclasses import confclass, unused, from_dict, save
import paramiko
from ssm_cli.xdg import get_conf_root, get_conf_file, get_ssh_hostkey
from ssm_cli.config import Config

import logging
from pathlib import Path
logger = logging.getLogger(__name__)

# 2 sets of defaults in this file, inside each action and in the SetupDefinitions default values, as sometimes it makes sense to have different defaults
# - The default in the action classes are for when the action is defined in a definitions file but no value is provided for that attribute
# - The default in the SetupDefinitions is for when the definitions file is not provided

# decorator to register the actions, saves having to do it manually. Lets also add confclasses here, saves space
actions = {}
def action(cls=None):
    def wrap(cls):
        cls = confclass(cls)
        actions[cls.action_name] = cls
        return cls
    return wrap(cls) if cls else wrap

@action
class ConfDirAction:
    action_name = "conf-dir"

    def run(self):
        root = get_conf_root(False)
        if root.exists():
            if not root.is_dir():
                raise FileExistsError(f"{root} already exists and is not a directory. Cleanup is likely needed.")
            print(f"{root} - skipping (already exists)")
            return
        
        print(f"{root} - creating directory")
        root.mkdir(511, True, True)

@action
class SshKeyGenAction:
    action_name = "ssh-keygen"

    def run(self):
        ssh_dir = Path.home() / ".ssh"
        key_files = list(ssh_dir.glob("id_*"))
        key_files = [f for f in key_files if f.is_file() and not f.name.endswith(".pub")]
        if key_files:
            print(f"SSH user key(s) already exist: {', '.join(str(f) for f in key_files)} - skipping (already exists)")
        else:
            print("No SSH user key found in ~/.ssh/id_* - generating new key pair")
            key_path = ssh_dir / "id_rsa"
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(str(key_path))
            pub_key = f"{key.get_name()} {key.get_base64()}\n"
            with open(str(key_path) + ".pub", "w") as pub_file:
                pub_file.write(pub_key)
            print(f"SSH key pair generated: {key_path} and {key_path}.pub")

@action
class SshDeployKeyAction:
    action_name = "ssh-deploy-key"
    group: str

@action
class SshHostKeyGenAction:
    action_name = "ssh-host-keygen"
    action_depends = ["conf-dir"]

    def run(self):
        path = get_ssh_hostkey(False)
        if path.exists():
            print(f"{path} - skipping (already exists)")
            return
        host_key = paramiko.RSAKey.generate(1024)
        host_key.write_private_key_file(path)
        print(f"{path} - created")



@action
class ConfFileAction:
    action_name = "conf-file"
    action_depends = ["conf-dir"]

    replace: bool = False
    merge: bool = False

    def run(self):
        path = get_conf_file(False)
        if path.exists() and not self.replace:
            print(f"{path} - skipping (already exists)")
            return
        
        # stop accidental polution of the config object, cannot see 
        # this being a real issue but better to be safe
        config = Config()
        from_dict(config, {})

        config.group_tag_key = input(f"What tag to use to split up the instances [{config.group_tag_key}]: ") or config.group_tag_key

        try:
            with path.open("w+") as file:
                save(config, file)
                print(f"{path} - created")
        except Exception as e:
            logger.error(e)
            path.unlink(True)

def get_action(action: str, args: dict = {}):
    obj = actions[action]()
    from_dict(obj, args)
    return obj

@confclass
class SetupDefinition:
    action: str

@confclass
class SetupDefinitions:
    definitions: List[SetupDefinition] = [
        {"action": "conf-dir"},
        {"action": "conf-file", "merge": True},
        {"action": "ssh-host-keygen"},
    ]

    def run(self):
        # convert into the objects
        execution_plan = []
        execution_actions = set()
        for definition in self.definitions:
            print(f"Adding {definition.action} to the execution plan")
            execution_plan.append(get_action(definition.action, unused(definition)))
            execution_actions.add(definition.action)
        
        # check for any dependencies
        for i, action in enumerate(execution_plan.copy()):
            for dep in getattr(action, "action_depends", []):
                if dep in execution_actions:
                    print(f"Action {action.action_name} depends on {dep} - already in the execution plan")
                else:
                    print(f"Action {action.action_name} depends on {dep} - adding to the execution plan")
                    execution_actions.add(dep)
                    execution_plan.insert(i, get_action(dep))
        
        # run the actions
        for action in execution_plan:
            action.run()