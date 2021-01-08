import consul
import grpc
import logging
import signal
import sys
import os
import argparse
import environ
import uuid
from concurrent import futures

import requests
from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)
from userop_service.proto import address_pb2, message_pb2, userfav_pb2, address_pb2_grpc, userfav_pb2_grpc, \
    message_pb2_grpc
from userop_service.handler.user_fav import UserFavServicer
from userop_service.handler.address import AddressServicer
from userop_service.handler.message import MessageServicer
from common.grpc_health.v1 import health_pb2, health_pb2_grpc
from common.grpc_health.v1 import health
from common.server import BaseServer
from userop_service.settings import settings


class UserOPServiceServer(BaseServer):
    SERVICE_NAME = "userop-srv"

    def __init__(self, host, port):
        super(UserOPServiceServer, self).__init__()
        self.SERVICE_ID = self.SERVICE_NAME + "-" + f'{str(uuid.uuid4())}'
        self.SERVICE_HOST = host
        self.SERVICE_PORT = port
        self.CONSUL_HOST = settings.data["consul"]["host"]
        self.CONSUL_PORT = settings.data["consul"]["port"]
        logger.add("logs/userop_service_{time}.log")

    def onExit(self, signo, frame):
        logger.info("User service terminate")
        self.unregister()
        sys.exit(0)

    def serve(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=40))
        address_pb2_grpc.add_AddressServicer_to_server(AddressServicer(), self.server)
        userfav_pb2_grpc.add_UserFavServicer_to_server(UserFavServicer(), self.server)
        message_pb2_grpc.add_MessageServicer_to_server(MessageServicer(), self.server)
        health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self.server)
        self.server.add_insecure_port(f'[::]:{self.SERVICE_PORT}')
        signal.signal(signal.SIGINT, self.onExit)
        signal.signal(signal.SIGTERM, self.onExit)
        logger.info("Start UserOP Srv Service at {}:{}".format(self.SERVICE_HOST, self.SERVICE_PORT))
        self.server.start()
        self.register()
        self.server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', nargs="?",
                        type=str,
                        default=settings.HOST,
                        help="host")
    parser.add_argument('--port',
                        nargs="?",
                        type=int,
                        default=50066,
                        help="port")
    args = parser.parse_args()
    server = UserOPServiceServer(args.host, args.port)
    server.serve()
