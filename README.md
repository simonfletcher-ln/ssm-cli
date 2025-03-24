# SSM CLI

A tool to make common tasks with SSM easier. The goal of this project is to help with the Session Manager, the tool tries to keep
the access it requires to a minimum.

## Installation & Setup

It can be installed with `pip install ssm-cli`, however most features rely on the session-manager-plugin being installed as well,
this is the standard way to make SSM connections. So a quick few steps here should be followed to avoid any issues.

### Step 1. Install Session Manager Plugin
You should be able to install it following the AWS documentation. Please see AWS documentation, to install it.
[Install the Session Manager plugin for the AWS CLI](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html).

### Step 2 (Optional). Install tkinter
ssm-cli makes use of tkinter for the UI selector, on windows this usualy comes pre built with the python binary. On WSL/Linux/MacOS
you may need to install it using the package manager for your distro, (for example with ubuntu `sudo apt install python3-tk`), further UI 
issues may occur with WSL, please see WSLg documentation on this [gui-apps](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)

### Step 3. Install ssm-cli

You can install this tool to a venv and it will work perfectly fine as well. However I recommend using the global or user space to
install it as it makes the ssm command available in default path.

```bash
pip install ssm-cli
```

### Step 4. run setup

> [!IMPORTANT]
> Do not skip this step!

The tool installs without any default config and will cause errors when it cannot find the config. To configure the tool
you must run the setup action. It will prompt asking for your grouping tag, more infomation on this [below](#grouping-tag).
```bash
ssm setup
# or
python -m ssm_cli setup
```

## AWS permissions

The tool uses boto3, so any standard `AWS_` environment variables can be used. Also the `--profile` option can be used similarly to aws cli.

You will need access to a few aws actions, below is a policy which should cover all features used by the tool. However
I recommend using conditions in some way to control fine grained access.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "FirstStatement",
        "Effect": "Allow",
        "Action": [
            "resourcegroupstaggingapi:GetResources",
            "ssm:DescribeInstanceInformation",
            "ssm:StartSession"
        ],
        "Resource": "*"
        }
    ]
}
```

# Config
This tool uses XDG standards on where to store its configuration. Typically this is `~/.confg/ssm-cli/` but when running setup it will output the location.

## Grouping tag
The selecting of instances revolves around a tag on the instance, the tag key can be configured using `group_tag_key`. The easiest way to test this is setup
properly is to use the `list` command:
```bash
# first list all groups
ssm list
# then list instances in those groups
ssm list my-group
```

# SSH Proxy

One advanced feature of ssm-cli is to use it to emulate an ssh tunnel to a remote. It does this by using the document [AWS-StartPortForwardingSessionToRemoteHost](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html#sessions-remote-port-forwarding) and a [paramiko server](https://docs.paramiko.org/en/stable/api/server.html).

## Example Setup

In this example we are forwarding connections to database.host via the instance with group=bastion_group. This same forwarding logic works with most tooling like dbeaver/datagrip/workbench. 
Adding to the ssh config (typically `~/.ssh/config`) and using ssh client as an example
```bash
cat >> ~/.ssh/config << EOL
Host bastion
    ProxyCommand ssm proxycommand bastion_group
EOL

ssh bastion -L 3306:database.host:3306 

# in another shell

mysql -h 127.0.0.1:3306 
```


