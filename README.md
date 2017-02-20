# Python-Crawl-UnityAssetStore
使用 [IPProxyTool](https://github.com/awolfly9/IPProxyTool) 获取的代理 IP 抓取 [Unity](https://unity3d.com/) 官方插件商店 [AssetStore](https://www.assetstore.unity3d.com/)。历时四个小时共抓取 [AssetStore](https://www.assetstore.unity3d.com/) 商店 34131 个插件信息。


##运行环境：
python 2.7.12
###运行依赖包
* scrapy
* mysql-connector-python
* requests

###Mysql 配置	
* 安装 Mysql 并启动
* 安装 mysql-connector-python [安装参考](http://stackoverflow.com/questions/31748278/how-do-you-install-mysql-connector-python-development-version-through-pip)
* 在 config.py 更改数据库配置
	
```
		database_config = {
    		'host': 'localhost',
    		'port': 3306,
    		'user': 'root',
    		'password': '123456',
		}
```
##下载使用
将项目克隆到本地

```
$ git clone https://github.com/awolfly9/unity.git
```

进入工程目录

```
$ cd unity
```

运行爬虫

```
$ python main.py
```
##项目说明
该项目默认使用 [IPProxyTool](https://github.com/awolfly9/IPProxyTool) 获取到的关于 unity [AssetStore](https://www.assetstore.unity3d.com/) 的代理抓取 assetstore 商店。
而且在使用时，确保 IPProxyTool 中验证出了有效的代理 IP。如果单纯测试爬虫不设置代理，可以在 [settings](https://github.com/awolfly9/unity/blob/master/unityassetstore/settings.py) 修改 IS_USE_PROXY = False 。

抓取到的完整数据已经上传到百度云，可以直接[下载](https://pan.baidu.com/share/init?shareid=206973657&uk=2639915701) （密码 base64：NzZudQ==） 后和 [exporttosql.py](https://github.com/awolfly9/unity/blob/master/exporttosql.py) 放置在同一目录，然后运行 [exporttosql.py](https://github.com/awolfly9/unity/blob/master/exporttosql.py) 导入数据库中。


##TODO
* 关于 assetstore 插件数据进行分析




