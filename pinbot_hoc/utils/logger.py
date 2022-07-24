import logging
from configs import Environments
from logging import getLogger, StreamHandler, Formatter


def setup_logger(name: str) -> logging.Logger:
    envs = Environments()

    logger = getLogger(name)
    handler = StreamHandler()
    handler.setLevel(envs.log_level)
    handler.setFormatter(Formatter(envs.log_format))
    logger.setLevel(envs.log_level)
    logger.addHandler(handler)

    return logger
