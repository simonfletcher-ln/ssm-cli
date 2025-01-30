from dataclasses import dataclass
from functools import cache
from typing import Dict, List
from ssm_cli.cli import ctx

import logging
logger = logging.getLogger(__name__)

@dataclass
class Instance():
    InstanceId: str
    NameTag: str
    IpAddress: str
    PingStatus: str

    def __str__(self):
        return f"{self.InstanceId} {self.IpAddress:<15} {self.PingStatus:<7} {self.NameTag}"


def get_resources(group_tag_value: str = None):
    logger.info("calling out to resourcegroupstaggingapi:GetResources")

    client = ctx.session.client('resourcegroupstaggingapi')
    tag_filter = {
        'Key': ctx.config.group_tag_key
    }
    if group_tag_value is not None:
         tag_filter['Values'] = [group_tag_value]

    logger.debug(f"filtering on {tag_filter}")
    response = client.get_resources(
        ResourceTypeFilters=[
            "ec2:instance"
        ],
        TagFilters=[tag_filter]
    )
    logger.debug(f"found {len(response['ResourceTagMappingList'])} resources")
    return response['ResourceTagMappingList']


def describe_instance_information(group_tag_value: str):
    logger.info("calling out to ssm:DescribeInstanceInformation")

    client = ctx.session.client('ssm')
    response = client.describe_instance_information(
         Filters=[
              {
                   'Key': f'tag:{ctx.config.group_tag_key}',
                   'Values': [group_tag_value]
              }
         ]
    )
    logger.debug(f"found {len(response['InstanceInformationList'])} instances")
    return response['InstanceInformationList']

def list_groups() -> List[str]:
    groups = set()
    for resource in get_resources():
        value = get_tag(resource['Tags'], ctx.config.group_tag_key)
        if value:
            groups.add(value)
    return sorted(list(groups))


def list_instances(group_tag_value: str) -> List[Instance]:
    instances = []
    instances_info = describe_instance_information(group_tag_value)
    resources = get_resources(group_tag_value)

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
