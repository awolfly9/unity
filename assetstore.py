#-*- coding: utf-8 -*-

import json
import logging
import os
import requests
import traceback
import sys
from SqlHelper import SqlHelper
from ExportToSql import insert_to_sql
from utils import *


class AssetStore(object):
    def __init__(self):
        self.unity_version = ''
        self.plugin_list = []
        self.sql = SqlHelper()

        self.table_name = 'unityassetstore'

        self.dir_plugins = 'Plugins/'
        self.dir_all = self.dir_plugins + 'all'
        make_dir(self.dir_plugins)
        make_dir(self.dir_all)

        self.cookies = None
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Host': 'www.assetstore.unity3d.com',
            'Referer': 'https://www.assetstore.unity3d.com/en/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
            'X-Kharma-Version': self.unity_version,
            'X-Requested-With': 'UnityAssetStore',
            'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
        }

    def run(self):
        create_table(self.sql, self.table_name)
        self.unity_version = self.get_untiy_version()
        self.headers['X-Kharma-Version'] = self.unity_version

        self.get_categories()

        self.get_plugin_list()

    def get_untiy_version(self):
        url = 'https://www.assetstore.unity3d.com/login'
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.assetstore.unity3d.com',
            'Referer': 'https://www.assetstore.unity3d.com/en/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 '
                          'Firefox/50.0',
            'X-Kharma-Version': '0',
            'X-Requested-With': 'UnityAssetStore',
            'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
        }

        formdata = {
            'current_package_id': '',
            'hardware_hash': '',
            'language_code': 'en',
            'license_hash': '',
        }

        r = requests.get(url, headers = headers, timeout = 20)
        log('get_unity_version text:\n%s' % r.text)

        data = json.loads(r.text)
        version = data.get('kharma_version')
        return version

    def get_categories(self):
        url = 'https://www.assetstore.unity3d.com/api/en-US/home/categories.json'
        r = requests.get(url = url, headers = self.headers, timeout = 20)
        self.cookies = r.cookies
        categories = json.loads(r.text)

        for category in categories.get('categories'):
            name = category.get('name', '')
            subs = category.get('subs', '')
            dir_name = self.dir_plugins + name
            make_dir(dir_name)

            if subs is not '':
                self.get_all_subs(subs, dir_name)
            else:
                # 提取信息
                name = category.get('name', '')
                count = category.get('count', 0)
                id = category.get('id', 0)
                child_subs = category.get('subs', '')

                plugin = {}
                plugin['name'] = name
                plugin['count'] = count
                plugin['id'] = id
                plugin['dir_name'] = dir_name
                if child_subs == '':
                    plugin['child'] = 'yes'
                else:
                    plugin['child'] = 'no'

                self.plugin_list.append(plugin)

    def get_plugin_list(self):
        for plugin in self.plugin_list:
            try:
                id = plugin.get('id', '')
                count = plugin.get('count')
                dir_name = plugin.get('dir_name')
                name = plugin.get('name')
                child = plugin.get('child')

                if child == 'no':
                    continue

                log('get_plugin_list plugin:%s' % plugin)

                if int(count) % 36 == 0:
                    page = int(count) / 36
                else:
                    page = int(count) / 36 + 1
                page = page + 1
                for i in range(1, page):
                    params = {
                        'q': 'category:%s' % id.encode(),
                        'rows': '36',
                        'page': i,
                        'order_by': 'popularity',
                        'engine': 'solr',
                    }

                    url = 'https://www.assetstore.unity3d.com/api/en-US/search/results.json'

                    for j in range(10):
                        try:
                            r = requests.get(url = url, params = params, headers = self.headers, timeout = 10)
                            log('get_plugin_list url:%s plugin:%s' % (r.url, str(plugin)))

                            file_name = dir_name + '/' + name + '_list.json'
                            self.write_file(file_name, r.text)

                            data = json.loads(r.text)
                            results = data.get('results')

                            self.get_plugin(dir_name, results)
                            break
                        except Exception, e:
                            if j == 9:
                                log('get_plugin_list exception getdata error msg:%s url:%s plugin:%s' % (
                                    e, url, str(plugin)), logging.ERROR)
                            else:
                                log('get_plugin_list exception getdata error msg:%s url:%s plugin:%s' % (
                                    e, url, str(plugin)), logging.WARNING)
                            continue

            except Exception, e:
                log('get_plugin_list exception get plugin list error msg:%s plugin:%s' % (e, str(plugin)))
                continue

    def get_plugin(self, dir_name, results):
        for result in results:
            name = result.get('title_english')
            name = name.replace('/', '_')
            id = result.get('id')
            rating = result.get('rating')
            count = rating.get('count', '')

            file_name = dir_name + '/' + id + '_' + name + '.json'
            if is_exists_sql(self.sql, id, self.table_name):
                self.get_plugin_comments(dir_name, name, id, count)
                continue

            for i in range(5):
                url = 'https://www.assetstore.unity3d.com/api/en-US/content/overview/%s.json' % id
                try:
                    r = requests.get(url = url, headers = self.headers, timeout = 10)
                    log('get_plugin url:%s ' % (url))

                    self.write_file(file_name, r.text)
                    self.get_plugin_comments(dir_name, name, id, count)
                    break
                except Exception, e:
                    if i == 4:
                        log('get_plugin exception msg:%s url:%s result:%s' % (e, url, str(result)), logging.ERROR)
                    else:
                        log('get_plugin exception msg:%s url:%s result:%s' % (e, url, str(result)),
                            logging.WARNING)
                    continue

    def get_plugin_comments(self, dir_name, name, id, count):
        file_name = dir_name + '/' + id + '_' + name + '_comments.json'
        if is_exists_sql(self.sql, id, self.table_name):
            return

        for i in range(5):
            'https://www.assetstore.unity3d.com/api/en-US/content/comments/368.json'
            url = 'https://www.assetstore.unity3d.com/api/en-US/content/comments/%s.json' % (id)
            try:
                r = requests.get(url = url, headers = self.headers, timeout = 10)
                log('get_plugin_comments url:%s dir_name:%s name:%s id:%s' % (url, dir_name, name, id))

                self.write_file(file_name, r.text)
                break
            except Exception, e:
                if i == 4:
                    log('get_plugin_comments exception msg:%s url:%s dir_name:%s name:%s id:%s' % (
                        e, url, dir_name, name, id), logging.ERROR)
                else:
                    log('get_plugin_comments exception msg:%s url:%s dir_name:%s name:%s id:%s' % (
                        e, url, dir_name, name, id), logging.WARNING)
                continue

        file_name = self.dir_all + '/' + id + '_' + name + '.json'
        insert_to_sql(self.sql, file_name, self.table_name)

    def get_all_subs(self, subs, dir):
        for sub in subs:
            #log(sub)

            # 提取信息
            name = sub.get('name', '')
            count = sub.get('count', 0)
            id = sub.get('id', 0)
            child_subs = sub.get('subs', '')

            # 处理数据
            dir_name = dir + '/' + name
            make_dir(dir_name)

            plugin = {}
            plugin['name'] = name
            plugin['count'] = count
            plugin['id'] = id
            plugin['dir_name'] = dir_name
            if child_subs == '':
                plugin['child'] = 'yes'
            else:
                plugin['child'] = 'no'

            self.plugin_list.append(plugin)

            if child_subs is not '':
                self.get_all_subs(child_subs, dir_name)

    def write_file(self, file_name, data):
        with open("%s" % file_name, 'w') as f:
            f.write(format_json(data))
            f.close()

        names = file_name.split('/')
        name = names[len(names) - 1]

        with open("%s/%s" % (self.dir_all, name), 'w') as f:
            f.write(format_json(data))
            f.close()

    def is_exists_plugin(self, dir, file_name):
        ret = os.path.exists('%s/%s' % (dir, file_name))
        log('is_exists_plugin ret:%s file_name:%s' % (ret, file_name))
        return ret


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    logging.basicConfig(
            filename = 'log/assetstore.log',
            format = '%(levelname)s %(asctime)s: %(message)s',
            level = logging.NOTSET
    )

    assetstore = AssetStore()
    assetstore.run()
