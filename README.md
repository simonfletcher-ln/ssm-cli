# SSM CLI

A tool to make common tasks with SSM easier. The goal of this project is to help with the Session Manager, the tool tries to keep the access it requires to a minimum.

## Installation

It can be installed with `pip install ssm-cli`, however most features rely on the session-manager-plugin being installed as well, this is the standard way to make SSM connections.

[AWS install guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

## AWS permission

The tool uses boto3, so any standard AWS_ environment variables can be used. Also the `--profile` option can be used.

You will need access to a few aws actions, below is a policy which should cover all features used by the tool.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "FirstStatement",
        "Effect": "Allow",
        "Action": [
            "resourcegroupstaggingapi:GetResources",
            "ssm:DescribeInstanceInformation"
        ],
        "Resource": "*"
        }
    ]
}
```
