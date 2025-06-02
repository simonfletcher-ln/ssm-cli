from dataclasses import dataclass, field
from functools import cache
import json
import re
import signal
import subprocess
import sys
from typing import Any, List

import boto3
from ssm_cli.selectors import SELECTORS
from ssm_cli.config import config

import logging
logger = logging.getLogger(__name__)


@dataclass
class Instance:
    """ Represents an EC2 instance """
    id: str
    name: str
    ip: str
    ping: str

    def __str__(self):
        return f"{self.id} {self.ip:<15} {self.ping:<7} {self.name}"
    
    def start_session(self, session):
        logger.debug(f"start session instance={self.id}")
        client = session.client('ssm')

        parameters = dict(
            Target=self.id
        )
        
        logger.info("calling out to ssm:StartSession")
        response = client.start_session(**parameters)
        logger.info(f"starting session: {response['SessionId']}")
        result = _session_manager_plugin([
            json.dumps({
                "SessionId": response["SessionId"],
                "TokenValue": response["TokenValue"],
                "StreamUrl": response["StreamUrl"]
            }),
            session.region_name,
            "StartSession",
            session.profile_name,
            json.dumps(parameters),
            f"https://ssm.{session.region_name}.amazonaws.com"
        ])
        if result != 0:
            logger.error(f"Failed to connect to session: {result.stderr.decode()}")
            raise RuntimeError(f"Failed to connect to session: {result.stderr.decode()}")   
    
    def start_port_forwarding_session_to_remote_host(self, session, host: str, remote_port: int, internal_port: int):
        logger.debug(f"start port forwarding between localhost:{internal_port} and {host}:{remote_port} via {self.id}")
        client = session.client('ssm')

        parameters = dict(
            Target=self.id,
            DocumentName='AWS-StartPortForwardingSessionToRemoteHost',
            Parameters={
                'host': [host],
                'portNumber': [str(remote_port)],
                'localPortNumber': [str(internal_port)]
            }
        )
        logger.info("calling out to ssm:StartSession")
        response = client.start_session(**parameters)

        logger.info(f"starting session: {response['SessionId']}")
        proc = subprocess.Popen(
            [
                "session-manager-plugin",
                json.dumps({
                    "SessionId": response["SessionId"],
                    "TokenValue": response["TokenValue"],
                    "StreamUrl": response["StreamUrl"]
                }),
                session.region_name,
                "StartSession",
                session.profile_name,
                json.dumps(parameters),
                f"https://ssm.{session.region_name}.amazonaws.com"
            ],
            stdout=subprocess.PIPE
        )

        for line in proc.stdout.readline():
            if line == b'Waiting for connections...':
                return



def _session_manager_plugin( command: list ) -> int:
    """ Call out to subprocess and ignore interrupts """
    if sys.platform == "win32":
        signals_to_ignore = [signal.SIGINT]
    else:
        signals_to_ignore = [signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP]

    original_signal_handlers = {}
    for sig in signals_to_ignore:
        original_signal_handlers[sig] = signal.signal(sig, signal.SIG_IGN)
    try:
        return subprocess.check_call(["session-manager-plugin", *command])
    finally:
        for sig, handler in original_signal_handlers.items():
            signal.signal(sig, handler)


class Instances:
    session: boto3.Session

    def __init__(self, session):
        self.session = session
        
    def select_instance(self, group_tag_value: str, selector: str) -> Instance:
        instances = sorted(self.list_instances(group_tag_value), key=lambda x: ip_as_int(x.ip))
        count = len(instances)
        if count == 1:
            return instances[0]
        if count < 1:
            return
        
        if selector not in SELECTORS:
            raise ValueError(f"invalid selector {selector}")
        
        self.selector = SELECTORS[selector]
        return self.selector(instances)

    def list_groups(self) -> List[str]:
        groups = set()
        for resource in self._get_resources():
            value = get_tag(resource['Tags'], config.group_tag_key)
            if value:
                groups.add(value)
        return sorted(list(groups))

    def list_instances(self, group_tag_value: str) -> List[Instance]:
        instances = []
        instances_info = self._describe_instance_information(group_tag_value)
        resources = self._get_resources(group_tag_value)

        for resource in resources:
            id = arn_to_instance_id(resource['ResourceARN'])
            name = get_tag(resource['Tags'], 'Name')
            for instance in instances_info:
                if instance['InstanceId'] == id:
                    instances.append(Instance(
                        id,
                        name,
                        instance['IPAddress'],
                        instance['PingStatus']
                    ))

        return instances

    def _get_resources(self, group_tag_value: str = None):
        logger.info("calling out to resourcegroupstaggingapi:GetResources")

        client = self.session.client('resourcegroupstaggingapi')
        paginator = client.get_paginator('get_resources')
        tag_filter = {
            'Key': config.group_tag_key
        }
        if group_tag_value is not None:
            tag_filter['Values'] = [group_tag_value]

        logger.debug(f"filtering on {tag_filter}")
        page_iter = paginator.paginate(
            ResourceTypeFilters=[
                "ec2:instance"
            ],
            TagFilters=[tag_filter]
        )
        total = 0
        for page in page_iter:
            for resource in page['ResourceTagMappingList']:
                total += 1
                yield resource
        logger.debug(f"yielded {total} resources")


    def _describe_instance_information(self, group_tag_value: str):
        logger.info("calling out to ssm:DescribeInstanceInformation")

        client = self.session.client('ssm')
        response = client.describe_instance_information(
            Filters=[
                {
                    'Key': f'tag:{config.group_tag_key}',
                    'Values': [group_tag_value]
                }
            ]
        )
        logger.debug(f"found {len(response['InstanceInformationList'])} instances")
        return response['InstanceInformationList']



def get_tag(tags: list, key: str) -> str:
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return None

@cache
def arn_to_instance_id(arn: str) -> str:
	parts = arn.split('/')
	if len(parts) != 2:
		raise ValueError(f"invalid instance arn {arn}")
	return parts[1]


def ip_as_int(ip: str) -> int:
    m = re.match(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', ip)
    if not m:
        raise ValueError(f"Invalid IP address: {ip}")
    return (int(m.group(1)) << 24) + (int(m.group(2)) << 16) + (int(m.group(3)) << 8) + int(m.group(4))
