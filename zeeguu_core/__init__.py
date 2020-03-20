# -*- coding: utf8 -*-
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(message)s")


def info(msg):
    logger.info(msg)


def log(msg):
    info(msg)


def warning(msg):
    logger.warning(msg)


def critical(msg):
    logger.critical(msg)
