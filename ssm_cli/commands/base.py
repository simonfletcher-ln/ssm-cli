from abc import ABC, abstractmethod
import argparse

import boto3

class BaseCommand(ABC):
    HELP: str = None
    
    @abstractmethod
    def add_arguments(parser: argparse.ArgumentParser):
        pass
    @abstractmethod
    def run(args: list, session: boto3.Session):
        pass