#-*- coding: utf-8 -*-

#-*- coding: utf-8 -*-
import json
import logging
import random

from Singleton import Singleton

import mysql.connector
from mysql.connector import errorcode
from utils import log
import traceback


class SqlHelper(Singleton):
    def __init__(self):
        self.database_name = 'assetstore'

        self.config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
        }

        self.init()

    def init(self):
        self.database = mysql.connector.connect(**self.config)
        self.cursor = self.database.cursor()

        self.create_database()
        self.database.database = self.database_name

    def create_database(self):
        try:
            self.cursor.execute('CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET \'utf8\' ' % self.database_name)
        except Exception, e:
            log('SqlHelper create_database exception:%s' % str(e), logging.WARNING)

    def create_table(self, command):
        try:
            self.cursor.execute(command)
            self.database.commit()
        except Exception, e:
            log('sql helper create_table exception:%s' % str(e), logging.WARNING)

    def insert_data(self, command, data):
        try:
            log('insert_data command:%s, data:%s' % (command, data))

            self.cursor.execute(command, data)
            self.database.commit()
        except Exception, e:
            log('sql helper insert_data exception msg:%s' % str(e), logging.WARNING)

    def execute(self, command):
        log('sql helper execute command:%s' % command)
        data = self.cursor.execute(command)
        return data
