import json

import environ
import nacos
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin
from loguru import logger

class ReconnectMySQLDataBase(PooledMySQLDatabase, ReconnectMixin):
    pass


"""
MYSQL_DB = "mxshop_user_srv"
MYSQL_HOST = "192.168.0.10"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "31415926"
"""

path = environ.Path(__file__) - 2
env = environ.Env()
environ.Env.read_env(path('.env'))

NACOS = {
    "Host": env.get_value("nacos_host"),
    "Port": env.get_value("nacos_port"),
    "NameSpace": env.get_value("nacos_namespace"),
    "User": "nacos",
    "Password": "nacos",
    "DataId": env.get_value("nacos_dataId"),
    "Group": env.get_value("nacos_group")
}


client = nacos.NacosClient(f"{NACOS['Host']}:{NACOS['Port']}", namespace=NACOS['NameSpace'],
                           username='nacos', password='nacos')

data = json.loads(client.get_config(NACOS["DataId"], NACOS["Group"]))

mysql_config = data['mysql']
DB = ReconnectMySQLDataBase(database=mysql_config['db'], host=mysql_config['host'], port=mysql_config['port'], user=mysql_config['user'],
                            password=mysql_config['password'])

HOST = data['host']
CONSUL_HOST = data['consul']['host']
CONSUL_POST = data['consul']['port']
Service_name = data['service_name']
logger.info(f"{Service_name} Read config from nacos " + f"{NACOS['Host']}:{NACOS['Port']}")
