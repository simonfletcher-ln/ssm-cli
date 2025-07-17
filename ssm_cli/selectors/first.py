import logging

logger = logging.getLogger()

def select(instances):
    for instance in instances:
        if instance.ping == "Online":
            return instance
    
    logger.error("No instance is has ping Online")
    return None