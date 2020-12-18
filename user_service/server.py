import grpc
import logging
import signal
import sys
import os
import argparse
import environ
from concurrent import futures
from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from user_service.proto import user_pb2_grpc
from user_service.handler.user import UserServicer
from common.grpc_health.v1 import health_pb2, health_pb2_grpc
from common.grpc_health.v1 import health

USER_SERVICE_HOST = None
USER_SERVICE_PORT = None


def onExit(signo, frame):
    logger.info("Process Terminate")
    sys.exit(0)

def read_config():
    path = environ.Path(__file__) - 1
    env = environ.Env()
    environ.Env.read_env(path('.env'))
    host = env.get_value('user_srv_host')
    port = int(env.get_value('user_srv_port'))
    return host, port

def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip',
                        nargs="?",
                        type=str,
                        default=USER_SERVICE_HOST,
                        help="ip")
    parser.add_argument('--port',
                        nargs="?",
                        type=int,
                        default=USER_SERVICE_PORT,
                        help="port")
    args = parser.parse_args()

    logger.add("logs/user_service_{time}.log")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServicer_to_server(UserServicer(), server)
    # 注册健康检查
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    server.add_insecure_port(f'[::]:{args.port}')

    # 主进程退出信号监听
    signal.signal(signal.SIGINT, onExit)
    signal.signal(signal.SIGTERM, onExit)
    logger.info("Start User Srv Service at {}:{}".format(args.ip, args.port))
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    USER_SERVICE_HOST, USER_SERVICE_PORT = read_config()
    serve()
