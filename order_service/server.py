import logging

import grpc
import signal
import sys
import os
import argparse
import environ
import uuid
from concurrent import futures
from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from order_service.proto import order_pb2_grpc
from order_service.handler.handler import OrderService
from order_service.settings import settings
from common.server import BaseServer
from common.grpc_health.v1 import health_pb2, health_pb2_grpc
from common.grpc_health.v1 import health


class OrderServiceServer(BaseServer):
    SERVICE_NAME = 'order-srv'

    def __init__(self, host, port):
        super(OrderServiceServer, self).__init__()
        self.SERVICE_ID = self.SERVICE_NAME + "-" + f'{str(uuid.uuid4())}'
        self.SERVICE_HOST = host
        self.SERVICE_PORT = port
        self.CONSUL_HOST = settings.data["consul"]["host"]
        self.CONSUL_PORT = settings.data["consul"]["port"]

    def onExit(self, signo, frame):
        logger.info("Order Service terminate")
        self.unregister()
        sys.exit(0)

    def serve(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=40))
        order_pb2_grpc.add_OrderServicer_to_server(OrderService(), self.server)
        health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self.server)
        self.server.add_insecure_port(f'[::]:{self.SERVICE_PORT}')
        signal.signal(signal.SIGINT, self.onExit)
        signal.signal(signal.SIGTERM, self.onExit)
        logger.info("Start Order Service at {}:{}".format(self.SERVICE_HOST, self.SERVICE_PORT))
        self.server.start()
        self.register()
        self.server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', nargs="?",
                        type=str,
                        default='192.168.0.14',
                        help="host")
    parser.add_argument('--port',
                        nargs="?",
                        type=int,
                        default=50063,
                        help="port")
    args = parser.parse_args()
    server = OrderServiceServer(args.host, args.port)
    server.serve()
