#-*- coding: utf-8 -*-

import logging
import utils
import config

from sqlhelper import SqlHelper

if __name__ == '__main__':
    logging.basicConfig(
            filename = 'log/exporttosql.log',
            format = '%(levelname)s %(asctime)s: %(message)s',
            level = logging.DEBUG
    )

    sql = SqlHelper()
    utils.create_table(sql, config.assetstore_table_name)
    utils.export_to_sql(sql, 'Plugins/all')
