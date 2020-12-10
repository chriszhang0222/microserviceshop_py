from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin


class ReconnectMySQLDataBase(PooledMySQLDatabase, ReconnectMixin):
    pass


MYSQL_DB = "mxshop_user_srv"
MYSQL_HOST = "192.168.0.17"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "31415926"

DB = ReconnectMySQLDataBase(database=MYSQL_DB, host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                            password=MYSQL_PASSWORD)
