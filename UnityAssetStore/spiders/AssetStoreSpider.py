# -*- coding: utf-8 -*-

import copy
import re
import json
import time
import os
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

	start_urls = [
		# unity asset store 所有分类的 json 地址
		'https://www.assetstore.unity3d.com/api/en-US/home/categories.json'
	]

	plugin_list = []

	dir_plugins = 'Plugins/'

	# TODO。。。 先获取版本信息
	headers = {
		'Accept': '*/*',
		'Accept-Encoding': 'gzip, deflate, br',
		'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
		'Connection': 'keep-alive',
		'Host': 'www.assetstore.unity3d.com',
		'Referer': 'https://www.assetstore.unity3d.com/en/',
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
		'X-Kharma-Version': '5.5.0-r87731',
		'X-Requested-With': 'UnityAssetStore',
		'X-Unity-Session': '26c4202eb475d02864b40827dfff11a14657aa41',
	}

	# 开始运行爬虫时调用
	def start_requests(self):
		for i, url in enumerate(self.start_urls):
			yield Request(
					url = url,
					meta = {
						'cookiejar': i
					},
					method = 'GET',
					headers = self.headers,
					callback = self.get_categories,
			)

	# 获取到分类的 json 文件
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

	# 获取到一页的插件
	def get_plugin_list(self, response):
		self.log('get_plugin_list:%s' % response.url)

		file_name = response.meta['dir_name'] + '/' + response.meta['name'] + '.json'
		self.write_file(file_name, self.format_json(response.body))

		dir_plugins = json.loads(response.body)
		results = dir_plugins.get('results', '')
		if results is not '':
			for plugin in results:
				id = plugin.get('id', '')
				'https://www.assetstore.unity3d.com/api/en-US/content/overview/19480.json'
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

	# 具体的获取到每一个插件，并存储获取到的 json 文件
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
				url = 'https://www.assetstore.unity3d.com/api/en-US/content/comments/' + id + '/' + count + '.json',
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
	def get_plugin_user_reviews(self, response):
		self.log('get_plugin_user_reviews:%s' % response.url)
		self.log('get_plugin_user_reviews:%s' % response.meta['dir_name'])
		file_name = response.meta['dir_name'] + '/' + response.meta['name'] + '_user_reviews.json'
		self.write_file(file_name, self.format_json(response.body))

		content = response.meta['content']
		title = response.meta['name']
		dir_name = response.meta['dir_name']

		images = content.get('images')
		for i, image in enumerate(images):
			link = image.get('link', '')
			if 'http' not in link:
				link = 'http:' + link
			self.log('link:%s' % link)
			name = image.get('name', title + '_' + str(i) + '.jpg')
			name = name.replace('/', '_')
			type = image.get('type', '')

			# 目前只下载所有截图，视频和模型，音频等暂时忽略
			# TODO...
			if type == 'screenshot':
				if link is not '' and link is not None:
					yield Request(
							url = link,
							method = 'GET',
							dont_filter = True,
							meta = {
								'dir_name': dir_name,
								'name': name,
								'cookiejar': response.meta['cookiejar'],
							},
							callback = self.get_plugin_image,
					)

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
