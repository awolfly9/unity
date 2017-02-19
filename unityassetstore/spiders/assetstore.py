# -*- coding: utf-8 -*-

import json
import logging
import config
import utils

from scrapy.spiders import Spider
from scrapy.http import Request, FormRequest
from proxymanager import proxymng
from sqlhelper import SqlHelper


class AssetStoreSpider(Spider):
    name = "assetstore"

    start_urls = [
        # 获取 unity 版本信息
        'https://www.assetstore.unity3d.com/login'
    ]

    def __init__(self, *a, **kwargs):
        super(AssetStoreSpider, self).__init__(*a, **kwargs)

        # 存储插件下载的目录
        self.dir_plugins = 'Plugins/'
        self.dir_all = self.dir_plugins + 'all'

        utils.make_dir(self.dir_plugins)
        utils.make_dir(self.dir_all)

        # 所有插件的一个列表
        self.plugin_list = []

        self.sql = SqlHelper()
        self.table_name = config.assetstore_table_name

        self.priority_adjust = 2

        # unity 的版本
        self.unity_version = ''

        # 请求 header
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

        utils.create_table(self.sql, self.table_name)

    # 开始运行爬虫时调用，请求 unity 版本信息
    def start_requests(self):
        for i, url in enumerate(self.start_urls):
            yield FormRequest(
                    url = url,
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
                    },
                    method = 'POST',
                    formdata = {
                        'current_package_id': '',
                        'hardware_hash': '',
                        'language_code': 'en',
                        'license_hash': '',
                    },
                    meta = {
                        'download_timeout': 20,
                        'is_proxy': False,
                    },
                    callback = self.get_unity_version,
            )

    #获取到 unity asset store 发布的版本，
    # 并发送请求分类的消息
    def get_unity_version(self, response):
        content = json.loads(response.body)
        utils.log('content:%s' % response.body)

        self.unity_version = content.get('kharma_version', '')
        self.headers['X-Kharma-Version'] = self.unity_version

        # unity asset store 所有分类的 json 地址
        url = 'https://www.assetstore.unity3d.com/api/en-US/home/categories.json'

        yield Request(
                url = url,
                method = 'GET',
                headers = self.headers,
                meta = {
                    'download_timeout': 20,
                    'is_proxy': False,
                },
                callback = self.get_categories,
        )

    # 获取到分类的 json 文件，并得到所有 unity 插件分类的列表
    # 提交请求每一个分类插件信息的消息
    def get_categories(self, response):
        self.write_file(self.dir_plugins + 'categories.json', response.body)

        # 加载分类的 json 文件
        categories = json.loads(response.body)

        for category in categories.get('categories'):
            name = category.get('name', '')
            subs = category.get('subs', '')
            dir_name = self.dir_plugins + name
            utils.make_dir(dir_name)

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

        for plugin in self.plugin_list:
            id = plugin.get('id', '')
            count = plugin.get('count')
            dir_name = plugin.get('dir_name')
            name = plugin.get('name')

            yield Request(
                    url = 'https://www.assetstore.unity3d.com/api/en-US/search/results.json?q=' + 'category:' + id + \
                          '&rows=' + count + '&page=' + str(1) + '&order_by=popularity' + '&engine=solr',
                    method = 'GET',
                    dont_filter = True,
                    headers = self.headers,
                    meta = {
                        'dir_name': dir_name,
                        'name': name,
                        'id': id,
                        'download_timeout': 60,
                        'is_proxy': False,
                    },
                    callback = self.get_plugin_list,
                    errback = self.error_parse,
            )

    # 获取一个类别的 unity 插件
    # 提交请求每一个插件的信息
    def get_plugin_list(self, response):
        utils.log('get_plugin_list url:%s  response meta:%s' % (response.url, response.meta))

        file_name = response.meta.get('dir_name') + '/' + response.meta.get('name') + '.json'
        self.write_file(file_name, response.body)

        dir_plugins = json.loads(response.body)
        results = dir_plugins.get('results', '')
        if results is not '':
            for plugin in results:
                id = plugin.get('id', '')

                url = 'https://www.assetstore.unity3d.com/api/en-US/content/overview/' + id + '.json'
                yield Request(
                        url = url,
                        meta = {
                            'dir_name': response.meta.get('dir_name'),
                            'id': id,
                            'download_timeout': 20,
                        },
                        headers = self.headers,
                        method = 'GET',
                        dont_filter = True,
                        callback = self.get_plugin,
                        errback = self.error_parse,
                )

    # 具体的获取到一个插件，并存储获取到的 json 文件
    # 请求获取插件的评论
    def get_plugin(self, response):
        utils.log('get_plugin url:%s  response meta:%s' % (response.url, response.meta))

        plugin = json.loads(response.body)

        id = response.meta.get('id')

        content = plugin.get('content', '')
        rating = content.get('rating')
        count = rating.get('count', '')

        dir_name = response.meta.get('dir_name')

        file_name = dir_name + '/' + id + '.json'
        self.write_file(file_name, response.body)

        # 获取插件的所有评论
        if count is '' or count is 'null' or count is None:
            count = 3

        yield Request(
                url = 'https://www.assetstore.unity3d.com/api/en-US/content/comments/' + id + '/' +
                      str(count) + '.json',
                method = 'GET',
                dont_filter = True,
                headers = self.headers,
                meta = {
                    'dir_name': dir_name,
                    'id': id,
                    'download_timeout': 10,
                },
                callback = self.get_plugin_comments,
                errback = self.error_parse,
        )

    # 获取插件的所有评论
    def get_plugin_comments(self, response):
        utils.log('get_plugin_comments:%s  response meta:%s' % (response.meta.get('dir_name'), response.meta))

        id = response.meta.get('id')

        file_name = response.meta.get('dir_name') + '/' + id + '_comments.json'
        self.write_file(file_name, response.body)

        file_name = self.dir_all + '/' + id + '.json'
        utils.insert_to_sql(self.sql, file_name, self.table_name)

    def get_all_subs(self, subs, dir):
        for sub in subs:
            #utils.log(sub)

            # 提取信息
            name = sub.get('name', '')
            count = sub.get('count', 0)
            id = sub.get('id', 0)
            child_subs = sub.get('subs', '')

            # 处理数据
            dir_name = dir + '/' + name
            utils.make_dir(dir_name)

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

    # 暂时不请求插件的图片
    # content = response.meta.get('#1')
    # title = response.meta.get('name')
    # dir_name = response.meta.get('dir_name')
    #
    # images = content.get('images')
    # for i, image in enumerate(images):
    # 	link = image.get('link', '')
    # 	if 'http' not in link:
    # 		link = 'http:' + link
    # 	utils.log('link:%s' % link)
    # 	name = image.get('name', title + '_' + str(i) + '.jpg')
    # 	name = name.replace('/', '_')
    # 	type = image.get('type', '')
    #
    # 	# 目前只下载所有截图.
    # 	# 视频和模型，音频等暂时忽略
    # 	# TODO...
    # 	if type == 'screenshot':
    # 		if link is not '' and link is not None:
    # 			yield Request(
    # 					url = link,
    # 					method = 'GET',
    # 					dont_filter = True,
    # 					meta = {
    # 						'dir_name': dir_name,
    # 						'name': name,
    # 					},
    # 					callback = self.get_plugin_image,
    # 			)


    # 获取插件的所有截图
    # def get_plugin_image(self, response):
    #     utils.log('get_plugin_image:%s' % response.url)
    #     utils.log('get_plugin_image:%s' % response.meta.get('dir_name'))
    #     dir_name = response.meta.get('dir_name')
    #     name = response.meta.get('name')
    #
    #     file_name = dir_name + '/' + name
    #     with open(file_name, 'wb') as f:
    #         f.write(response.body)
    #         f.close()

    def error_parse(self, failure):
        request = failure.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta), logging.ERROR)

        proxy = request.meta.get('proxy', None)
        if proxy:
            proxymng.delete_proxy(proxy)
            request.meta['proxy'] = proxymng.get_proxy()

        request.priority = request.priority + self.priority_adjust
        yield request

    def write_file(self, file_name, data):
        with open("%s" % file_name, 'w') as f:
            f.write(utils.format_json(data))
            f.close()

        names = file_name.split('/')
        name = names[len(names) - 1]

        with open("%s/%s" % (self.dir_all, name), 'w') as f:
            f.write(utils.format_json(data))
            f.close()
