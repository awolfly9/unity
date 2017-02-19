#-*- coding: utf-8 -*-

import json
import logging
import os
from utils import log
from sqlhelper import SqlHelper

if __name__ == '__main__':
    logging.basicConfig(
            filename = 'main.log',
            format = '%(levelname)s %(asctime)s: %(message)s',
            level = logging.NOTSET
    )
