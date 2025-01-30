import argparse
import boto3
from ssm_cli.config import Config

class Context:
    session: boto3.Session
    args: argparse.Namespace
    config: Config
    