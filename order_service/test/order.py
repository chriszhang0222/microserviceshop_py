import consul
import grpc
from order_service.proto import order_pb2_grpc, order_pb2
from order_service.settings import settings


class OrderTest:
    def __init__(self):
        c = consul.Consul(host=settings.CONSUL_HOST, port=settings.CONSUL_POST)
        services = c.agent.services()
        ip, port = None, None
        for key, value in services.items():
            if value["Service"] == settings.Service_name:
                ip = value['Address']
                port = value['Port']
                break
        if not ip or not port:
            raise Exception()
        channel = grpc.insecure_channel(f"{ip}:{port}")
        self.order_stub = order_pb2_grpc.OrderStub(channel)

    def create_cart_item(self):
        rsp = self.order_stub.CreateCartItem(order_pb2.CartItemRequest(
            goodsId=421, userId=1, nums=2
        ))
        print(rsp)