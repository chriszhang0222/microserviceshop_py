import grpc
import logging
from concurrent import futures
from loguru import logger
from user_service.proto import user_pb2_grpc, user_pb2
from user_service.handler.user import UserServicer


def serve():
    logger.add("logs/user_service_{time}.log")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServicer_to_server(UserServicer(), server)
    server.add_insecure_port('[::]:50052')
    logger.info("start service")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
