# coding=utf-8
import base64
import random
import requests
import json
import logging

class ProxyMiddleware(object):
    def process_request(self, request, spider):
        contents = requests.get('http://127.0.0.1:8000/?types=0&count=5&country=%E4%B8%AD%E5%9B%BD')
        print('contents:%s' % contents.text)
        data = json.loads(contents.text)
        proxy = random.choice(data)
        # if proxy['user_pass'] is not None:
        #     request.meta['proxy'] = "http://%s" % proxy['ip_port']
        #     encoded_user_pass = base64.encodestring(proxy['user_pass'])
        #     request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass
        #     print "**************ProxyMiddleware have pass************" + proxy['ip_port']
        # else:
        print "**************ProxyMiddleware no pass************" + proxy.get('ip')
        ip = proxy.get('ip')
        port = proxy.get('port')
        address = str(ip) + ':' + str(port)
        #request.meta['proxy'] = "http://%s" % proxy['ip_port']
        request.meta['proxy'] = "http://%s" % address
        print('proxy:%s' % request.meta['proxy'] )



#
#
# PROXIES = [
#     {'ip_port': '111.11.228.75:80', 'user_pass': ''},
#     {'ip_port': '120.198.243.22:80', 'user_pass': ''},
#     {'ip_port': '111.8.60.9:8123', 'user_pass': ''},
#     {'ip_port': '101.71.27.120:80', 'user_pass': ''},
#     {'ip_port': '122.96.59.104:80', 'user_pass': ''},
#     {'ip_port': '122.224.249.122:8088', 'user_pass': ''},
# ]