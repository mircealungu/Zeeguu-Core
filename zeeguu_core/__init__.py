# -*- coding: utf8 -*-
import os

import datetime

log_file = "zeeguu.log"

log_dir = os.getenv('ZEEGUU_CORE_LOG_DIR')
if log_dir:

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = f"{log_dir}/{log_file}"


def log(text):
    text = f'{datetime.datetime.now()} {text}'

    with open(log_file, "a", encoding='utf-8') as file:
        file.write(f'{text}\n')
    return text


def logp(text):
    """

        Log and print to stdout at the same time

    :return: None
    """
    print(log(text))
