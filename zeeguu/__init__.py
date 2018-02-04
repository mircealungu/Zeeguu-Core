# -*- coding: utf8 -*-
import os

import datetime

log_file = os.path.expanduser("~/.config/zeeguu/zeeguu_log.txt")


def log(text):
    text = str(datetime.datetime.now()) + text
    with open(log_file, "a", encoding='utf-8') as myfile:
        myfile.write((text + "\n"))
    return text


def log_n_print(text):
    print(log(text))
