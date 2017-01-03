# -*- coding: utf-8 -*-
import os
import re
import json
import time
from scrapy.spiders import Spider
from scrapy.http import Request, FormRequest


class AssetStoreSpider(Spider):
    name = "assetstore"

    start_urls = [
        #获取 unity 版本信息
        'https://www.assetstore.unity3d.com/login'
    ]

    # 所有插件的一个列表
    plugin_list = []

    # 存储插件下载的目录
    dir_plugins = 'Plugins/'
    dir_all = 'Plugins/all'

    # unity 的版本
    unity_version = ''

    # 请求 header
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Host': 'www.assetstore.unity3d.com',
        'Referer': 'https://www.assetstore.unity3d.com/en/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
        'X-Kharma-Version': unity_version,
        'X-Requested-With': 'UnityAssetStore',
        'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
    }

    # 开始运行爬虫时调用，请求 unity 版本信息
    def start_requests(self):

        self.make_dir(self.dir_plugins)
        self.make_dir(self.dir_all)

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
                        'cookiejar': i
                    },
                    callback = self.get_unity_version,
            )

    #获取到 unity asset store 发布的版本，
    # 并发送请求分类的消息
    def get_unity_version(self, response):
        content = json.loads(response.body)
        self.log('content:%s' % response.body)
        self.unity_version = content.get('kharma_version', '')
        self.headers['X-Kharma-Version'] = self.unity_version

        # unity asset store 所有分类的 json 地址
        url = 'https://www.assetstore.unity3d.com/api/en-US/home/categories.json'

        yield Request(
                url = url,
                meta = {
                    'cookiejar': response.meta['cookiejar'],
                },
                method = 'GET',
                headers = self.headers,
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
            self.make_dir(dir_name)

            if subs is not '':
                self.get_all_subs(subs, dir_name, response)

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
                        'cookiejar': response.meta['cookiejar'],
                        'dir_name': dir_name,
                        'name': name,
                    },
                    callback = self.get_plugin_list,
            )

    # ###
    def get_all_subs(self, subs, dir, response):
        for sub in subs:
            #self.log(sub)

            # 提取信息
            name = sub.get('name', '')
            count = sub.get('count', 0)
            id = sub.get('id', 0)
            child_subs = sub.get('subs', '')

            # 处理数据
            dir_name = dir + '/' + name
            self.make_dir(dir_name)

            plugin = {}
            plugin['name'] = name
            plugin['count'] = count
            plugin['id'] = id
            plugin['dir_name'] = dir_name

            self.plugin_list.append(plugin)

            if child_subs is not '':
                self.get_all_subs(child_subs, dir_name, response)

    # 获取一个类别的 unity 插件
    # 提交请求每一个插件的信息
    def get_plugin_list(self, response):
        self.log('get_plugin_list:%s' % response.url)

        file_name = response.meta['dir_name'] + '/' + response.meta['name'] + '.json'
        self.write_file(file_name, self.format_json(response.body))

        dir_plugins = json.loads(response.body)
        results = dir_plugins.get('results', '')
        if results is not '':
            for plugin in results:
                id = plugin.get('id', '')
                'https://www.assetstore.unity3d.com/api/en-US/content/overview/368.json'
                url = 'https://www.assetstore.unity3d.com/api/en-US/content/overview/' + id + '.json'
                yield Request(
                        url = url,
                        meta = {
                            'cookiejar': response.meta['cookiejar'],
                            'dir_name': response.meta['dir_name'],
                            'id': id,
                        },
                        headers = self.headers,
                        method = 'GET',
                        dont_filter = True,
                        callback = self.get_plugin_json,
                )

    # 具体的获取到一个插件，并存储获取到的 json 文件
    # 请求获取插件的评论
    def get_plugin_json(self, response):
        plugin = json.loads(response.body)
        content = plugin.get('content', '')
        title = content.get('title')
        title = title.replace('/', '_')

        dir_name = response.meta['dir_name']
        dir_name = dir_name + '/' + title
        self.make_dir(dir_name)

        file_name = dir_name + '/' + title + '.json'
        self.write_file(file_name, self.format_json(response.body))

        rating = content.get('rating')
        count = rating.get('count', '')
        id = response.meta['id']

        # 获取插件的所有评论
        if count is not '' and count is not 'null' and count is not None:
            yield Request(
                    #'https://www.assetstore.unity3d.com/api/en-US/content/comments/61491/3.json'
                    url = 'https://www.assetstore.unity3d.com/api/en-US/content/comments/' + id + '/' + count +
                          '.json',
                    method = 'GET',
                    dont_filter = True,
                    headers = self.headers,
                    meta = {
                        'dir_name': dir_name,
                        'name': title,
                        'content': content,
                        'cookiejar': response.meta['cookiejar'],
                    },
                    callback = self.get_plugin_user_reviews,
            )

    # 获取插件的所有评论
    # 并请求插件的所有屏幕截图
    def get_plugin_user_reviews(self, response):
        self.log('get_plugin_user_reviews:%s' % response.meta['dir_name'])
        file_name = response.meta['dir_name'] + '/' + response.meta['name'] + '_user_reviews.json'
        self.write_file(file_name, self.format_json(response.body))

    # 暂时不请求插件的图片
    # content = response.meta['content']
    # title = response.meta['name']
    # dir_name = response.meta['dir_name']
    #
    # images = content.get('images')
    # for i, image in enumerate(images):
    # 	link = image.get('link', '')
    # 	if 'http' not in link:
    # 		link = 'http:' + link
    # 	self.log('link:%s' % link)
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
    # 						'cookiejar': response.meta['cookiejar'],
    # 					},
    # 					callback = self.get_plugin_image,
    # 			)


    # 获取插件的所有截图
    def get_plugin_image(self, response):
        self.log('get_plugin_image:%s' % response.url)
        self.log('get_plugin_image:%s' % response.meta['dir_name'])
        dir_name = response.meta['dir_name']
        name = response.meta['name']

        file_name = dir_name + '/' + name
        with open(file_name, 'wb') as f:
            f.write(response.body)
            f.close()

    def make_dir(self, dir):
        self.log('make dir:%s' % dir)
        if not os.path.exists(dir):
            os.makedirs(dir)

    def format_json(self, data):
        return json.dumps(json.loads(data), indent = 4)

    def write_file(self, file_name, data):
        with open("%s" % file_name, 'w') as f:
            f.write(self.format_json(data))
            f.close()

        names = file_name.split('/')
        name = names[len(names) - 1]

        with open("%s/%s" % (self.dir_all, name) , 'w') as f:
            f.write(self.format_json(data))
            f.close()

