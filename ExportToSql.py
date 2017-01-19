#-*- coding: utf-8 -*-

import json
import logging
import os
from utils import log
from SqlHelper import SqlHelper
from config import *
from utils import *

if __name__ == '__main__':
    logging.basicConfig(
            filename = 'main.log',
            format = '%(levelname)s %(asctime)s: %(message)s',
            level = logging.NOTSET
    )
