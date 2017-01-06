#-*- coding: utf-8 -*-

import logging
import traceback

from bs4 import CData
from bs4 import NavigableString


def log(msg, level = logging.DEBUG):
    logging.log(level, msg)
    print('level:%s, msg:%s' % (level, msg))

    if level == logging.WARNING or level == logging.ERROR:
        for line in traceback.format_stack():
            print(line.strip())

        for line in traceback.format_stack():
            logging.log(level, line.strip())


def get_first_text(soup, strip = False, types = (NavigableString, CData)):
    data = None
    for s in soup._all_strings(strip, types = types):
        data = s
        break
    return data


def get_texts(soup, strip = False, types = (NavigableString, CData)):
    texts = []
    for s in soup._all_strings(strip, types = types):
        texts.append(s)

    return texts
