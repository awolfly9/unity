#-*- coding: utf-8 -*-

import json
import logging
import os
from utils import log
from SqlHelper import SqlHelper

dir_plugins = 'Plugins/'
dir_all = dir_plugins + 'all'
table_name = 'unityassetstore'

sql = SqlHelper()


def create_table():
    commond = ("CREATE TABLE IF NOT EXISTS {} ("
               "`id` INT(6) NOT NULL PRIMARY KEY UNIQUE,"
               "`name` TEXT NOT NULL,"
               "`asset_url` TEXT DEFAULT NULL,"
               "`rating_count` INT(4) DEFAULT 0,"
               "`rating_comments_count` INT(4) DEFAULT 0,"
               "`rating_comments_ratio` FLOAT DEFAULT 0.0,"
               "`rating_average` INT(4) DEFAULT 0,"
               "`rating_five` INT(4) DEFAULT 0,"
               "`rating_five_ratio` FLOAT(4) DEFAULT 0.0,"
               "`rating_four` INT(4) DEFAULT 0,"
               "`rating_three` INT(4) DEFAULT 0,"
               "`rating_two` INT(4) DEFAULT 0,"
               "`rating_one` INT(4) DEFAULT 0,"
               "`pubdate` TEXT NOT NULL,"
               "`category` TEXT NOT NULL,"
               "`version` TEXT NOT NULL,"
               "`price_USD` FLOAT DEFAULT NULL,"
               "`price_JPY` FLOAT DEFAULT NULL,"
               "`price_DKK` FLOAT DEFAULT NULL,"
               "`price_EUR` FLOAT DEFAULT NULL,"
               "`sizetext` TEXT DEFAULT NULL,"
               "`publisher_name` TEXT DEFAULT NULL,"
               "`publisher_url` TEXT DEFAULT NULL,"
               "`publisher_support_url` TEXT DEFAULT NULL,"
               "`publisher_email` TEXT DEFAULT NULL,"
               "`first_published_at` TEXT DEFAULT NULL"
               ") ENGINE=InnoDB".format(table_name))

    sql.create_table(commond)


def export_to_sql():
    for i, file in enumerate(os.listdir(dir_all)):
        file_name = '%s/%s' % (dir_all, file)
        log('export_to_sql file_name:%s' % file_name)

        insert_to_sql(file_name)


def insert_to_sql(file_name):
    names = file_name.split('_')
    if names[len(names) - 1] == 'list.json' or names[len(names) - 1] == 'comments.json':
        return

    if file_name.find('.json') == -1:
        return

    log('insert_to_sql file_name:%s' % file_name)

    with open(file_name, 'r') as f:
        plugin_source = f.read()
        f.close()

    plugin = json.loads(plugin_source)
    content = plugin.get('content')
    id = content.get('id', '')
    name = content.get('title', '')
    asset_url = 'https://www.assetstore.unity3d.com/en/#!/content/%s' % id

    rating = content.get('rating', '')
    rating_count = rating.get('count', '0')
    if rating_count == None:
        rating_count = 0
    rating_average = rating.get('average', '0')

    pubdate = content.get('pubdate', '')

    category = content.get('category', '')
    category_lable = category.get('label', '')

    version = content.get('version')

    price = content.get('price', '')
    if price == '':
        price_USD = 0
        price_JPY = 0
        price_DKK = 0
        price_EUR = 0
    else:
        price_USD = price.get('USD', '0')
        price_JPY = price.get('JPY', '0')
        price_DKK = price.get('DKK', '0')
        price_EUR = price.get('EUR', '0')

    sizetext = content.get('sizetext', '')

    publisher = content.get('publisher', '')
    publisher_name = publisher.get('label', '')
    publisher_url = publisher.get('url', '')
    publisher_support_url = publisher.get('support_url', '')
    publisher_email = publisher.get('support_email', '')

    first_published_at = content.get('first_published_at', '')

    rating_comments_count = 0
    rating_comments_ratio = 0

    rating_five = 0
    rating_five_ratio = 0
    rating_four = 0
    rating_three = 0
    rating_two = 0
    rating_one = 0

    comment_file_name = '%s_%s' % (file_name[:-5], 'comments.json')
    if os.path.exists(comment_file_name):
        with open(comment_file_name, 'r') as f:
            comment_source = f.read()
            f.close()

        plugin_comments = json.loads(comment_source)
        comments = plugin_comments.get('comments', '')
        rating_comments_count = plugin_comments.get('count', '0')
        if rating_count != None and rating_count != '0' and rating_count != 0:
            rating_comments_ratio = int(rating_comments_count) * 1.0 / int(rating_count)

        rating_five = comment_source.count('"rating": "5"')
        if rating_comments_count != None and rating_comments_count != '0' and rating_comments_count != 0:
            rating_five_ratio = int(rating_five) * 1.0 / int(rating_comments_count)
        rating_four = comment_source.count('"rating": "4"')
        rating_three = comment_source.count('"rating": "3"')
        rating_two = comment_source.count('"rating": "2"')
        rating_one = comment_source.count('"rating": "1"')

    command = ("INSERT IGNORE INTO {} "
               "(id, name, asset_url, rating_count, rating_comments_count, rating_comments_ratio, "
               "rating_average, rating_five, rating_five_ratio, rating_four, rating_three, "
               "rating_two, rating_one, pubdate, category, version, price_USD, price_JPY, price_DKK, "
               "price_EUR, sizetext, publisher_name, publisher_url, publisher_support_url, publisher_email, "
               "first_published_at)"
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
               "%s, %s, %s, %s, %s)".format(table_name))

    msg = (id, name, asset_url, rating_count, rating_comments_count, rating_comments_ratio, rating_average,
           rating_five, rating_five_ratio, rating_four, rating_three, rating_two, rating_one, pubdate,
           category_lable,
           version, price_USD, price_JPY, price_DKK, price_EUR, sizetext, publisher_name,
           publisher_url, publisher_support_url, publisher_email, first_published_at)

    sql.insert_data(command, msg)


if __name__ == '__main__':
    logging.basicConfig(
            filename = 'main.log',
            format = '%(levelname)s %(asctime)s: %(message)s',
            level = logging.NOTSET
    )

    create_table()
    export_to_sql()
