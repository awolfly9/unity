# coding=utf-8

import logging
from scrapy import cmdline

logging.basicConfig(
        filename= 'log/mian.log',
        format='%(levelname)s %(asctime)s: %(message)s',
        level=logging.DEBUG
    )

cmdline.execute("scrapy crawl assetstore".split())