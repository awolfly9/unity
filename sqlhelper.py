#-*- coding: utf-8 -*-

#-*- coding: utf-8 -*-
import json
import logging
import random
import traceback
import mysql.connector

from singleton import Singleton
from mysql.connector import errorcode
from utils import log
from config import *


class SqlHelper(Singleton):
    def __init__(self):
        self.database_name = database_name
        self.init()

    def init(self):
        self.database = mysql.connector.connect(**database_config)
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
