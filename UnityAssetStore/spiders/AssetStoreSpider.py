# -*- coding: utf-8 -*-

import copy
import re
import json
import time
from scrapy.selector import Selector
from scrapy.spiders import Spider
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.sgml import SgmlLinkExtractor as sle
from scrapy.http.cookies import CookieJar
from scrapy.http import Request, FormRequest

class AssetStoreSpider(Spider):
    name = "assetstore"

    # 开始运行爬虫是调用
    def start_requests(self):
        # 获取分类的 json 文件的 url 地址
        urls = [
            "https://www.assetstore.unity3d.com/api/en-US/home/categories.json"
        ]

        for i, url in enumerate(urls):
            yield Request(
                url=url,
                meta={'cookiejar': i},
                method = 'GET',
                headers={
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Host': 'www.assetstore.unity3d.com',
                    'Referer': 'https://www.assetstore.unity3d.com/en/',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
                    'X-Kharma-Version': '5.4.0-r87646',
                    'X-Requested-With': 'UnityAssetStore',
                    'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
                },
                callback=self.get_categories
            )

    # 获取到分类的 json 文件
    def get_categories(self, response):

        self.write_file('categories.json', response.body)

        #加载分类的 json 文件
        categories = json.loads(response.body)

        # 从具体的搜索页面中重新获取所有的分类的 json 文件，第一次获取的插件数量不对
        for category in categories['categories']:
            name = category['name']
            id = category['id']
            url = 'https://www.assetstore.unity3d.com/api/en-US/search/results.json?q=' + 'category:' + id + '&rows=36' + \
                  '&page=' + str(1) + '&order_by=popularity' + '&engine=solr'

            yield Request(
                url = url,
                meta = {
                    'cookiejar': response.meta['cookiejar'],
                    'file_name': category['name'],
                    'category': id,
                    'name': category['name'],
                },
                method = 'GET',
                dont_filter = True,
                headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Host': 'www.assetstore.unity3d.com',
                    'Referer': 'https://www.assetstore.unity3d.com/en/',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
                    'X-Kharma-Version': '5.4.0-r87646', 'X-Requested-With': 'UnityAssetStore',
                    'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
                },
                callback = self.get_category_plugin_count
            )

    # 获取每一个分类的插件的数量，并分页获取插件，一次性获取 36 个插件
    def get_category_plugin_count(self, response):
        #print('get_category_plugin_count proxy:%s' % response.meta['proxy'])
        category = json.loads(response.body)
        total = category['total']
        self.log('category total:' + str(total))

        # 以每页 36 个插件读取
        page_count = total / 36
        if total % 36 != 0:
            page_count = page_count + 1

        for page in range(1, page_count + 1):
            id = response.meta['category']
            url = 'https://www.assetstore.unity3d.com/api/en-US/search/results.json?q=' + 'category:' + id + '&rows=36' + \
                  '&page=' + str(page) + '&order_by=popularity' + '&engine=solr'

            yield Request(
                    url = url,
                    meta = {
                        'cookiejar': response.meta['cookiejar'],
                        'file_name': response.meta['name'] + '_' + str(page),
                    },
                    method = 'GET',
                    dont_filter = True,
                    headers = {
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Cache-Control': 'max-age=0',
                        'Connection': 'keep-alive',
                        'Host': 'www.assetstore.unity3d.com',
                        'Referer': 'https://www.assetstore.unity3d.com/en/',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
                        'X-Kharma-Version': '5.4.0-r87646',
                        'X-Requested-With': 'UnityAssetStore',
                        'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
                    },

                    callback = self.get_plugin_list
                )

    # 获取到一页的插件
    def get_plugin_list(self, response):
        #self.log('get_plugin_list:\n' + response.body)

        file_name = response.meta['file_name'].replace(u'/', u'_')
        self.write_file('log/%s.json' % response.meta['file_name'], response.body)

        plugins = json.loads(response.body)

        for plugin in plugins['results']:
            id = plugin['id']

            url = 'https://www.assetstore.unity3d.com/api/en-US/content/overview/' + id + '.json'
            yield Request(url = url,
                meta = {
                    'cookiejar': response.meta['cookiejar'],
                    'file_name': id + '_' + plugin['title'],
                },
                headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Host': 'www.assetstore.unity3d.com',
                    'Referer': 'https://www.assetstore.unity3d.com/en/',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
                    'X-Kharma-Version': '5.4.0-r87646',
                    'X-Requested-With': 'UnityAssetStore',
                    'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
                },
                method = 'GET',
                dont_filter = True, callback = self.get_plugin
            )

    # 具体的获取到每一个插件，并存储获取到的 json 文件
    def get_plugin(self, response):
        file_name = response.meta['file_name'].replace(u'/', u'_')
        self.write_file('plugin/%s.json' % file_name, response.body)
    #
    #     plugin = json.loads(response.body)
    #     content = plugin.get('content', '')
    #     #self.log('key_image:' + str(key_image))
    #     key_image = content['keyimage']
    #     #self.log('key_image:' + str(key_image))
    #     icon = key_image['icon75']
    #     'http://d2ujflorbtfzji.cloudfront.net/key-image/9e17b026-08c0-4f8e-b7cd-53176a3104d6.png'
    #     self.log('icon:' + icon)
    #     names = str(icon).split(u'/')
    #     name = names[len(names) - 1]
    #     icon = 'http:'+ icon
    #
    #     yield Request(
    #         url = icon,
    #         headers = {
    #             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #             'Accept-Encoding': 'gzip, deflate',
    #             'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    #             'Connection': 'd2ujflorbtfzji.cloudfront.net',
    #             'Upgrade-Insecure-Requests': '1',
    #             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
    #         },
    #         meta = {
    #             'cookiejar': response.meta['cookiejar'],
    #             'file_name': name,
    #         },
    #         method = 'GET',
    #         dont_filter = True,
    #         callback = self.get_icon
    #
    #     )
    #
    # def get_icon(self, response):
    #     #self.log(response.body)
    #     with open('img/%s' % response.meta['file_name'], 'w') as f:
    #         f.write(response.body)
    #         f.close()

    def format_json(self, data):
        return json.dumps(json.loads(data), indent = 4)

    def write_file(self, file_name, data):
        with open("%s" % file_name, 'w') as f:
            f.write(self.format_json(data))
            f.close()
