# coding=utf-8

import logging
import os

from scrapy import cmdline

if not os.path.exists('log'):
    os.makedirs('log')

logging.basicConfig(
        filename = 'log/main.log',
        format = '%(levelname)s %(asctime)s: %(message)s',
        level = logging.DEBUG
)

cmdline.execute("scrapy crawl assetstore".split())
