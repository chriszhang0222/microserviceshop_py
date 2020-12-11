import grpc
import logging
import signal
import sys
import os
import argparse
from concurrent import futures
from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from user_service.proto import user_pb2_grpc
from user_service.handler.user import UserServicer


def onExit(signo, frame):
    logger.info("Process Terminate")
    sys.exit(0)


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip',
                        nargs="?",
                        type=str,
                        default="127.0.0.1",
                        help="ip")
    parser.add_argument('--port',
                        nargs="?",
                        type=int,
                        default="50052",
                        help="port")
    args = parser.parse_args()

    logger.add("logs/user_service_{time}.log")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServicer_to_server(UserServicer(), server)

    # 主进程退出信号监听
    signal.signal(signal.SIGINT, onExit)
    signal.signal(signal.SIGTERM, onExit)
    server.add_insecure_port(f'[::]:{args.port}')
    logger.info("start service {}:{}".format(args.ip, args.port))
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
