# -*- coding: utf8 -*-
import os

import datetime

log_file = os.path.expanduser("~/.config/zeeguu/zeeguu_log.txt")


def log(text):
    text = f'{datetime.datetime.now()} {text}'

    with open(log_file, "a", encoding='utf-8') as file:
        file.write(f'{text}\n')
    return text


def log_n_print(text):
    """

        Print both to stdout and the logfile

    :return: None
    """
    print(log(text))
