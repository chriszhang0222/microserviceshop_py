import grpc
from order_service.proto import order_pb2, order_pb2_grpc
from loguru import logger
from order_service.model.model import *
from google.protobuf import empty_pb2

class OrderService(order_pb2_grpc.OrderServicer):

    @logger.catch
    def CartItemList(self, request: order_pb2.UserInfo, context):
        items = ShoppingCart.select().where(ShoppingCart.user==request.id)
        rsp = order_pb2.CartItemListResponse()
        rsp.total = items.count()
        for item in items:
            item_rsp = order_pb2.ShopCartInfoResponse()
            item_rsp.id = item.id
            item_rsp.userId = item.user
            item_rsp.goodsId = item.goodsId
            item_rsp.nums = item.nums
            items.checked = item.checked
            rsp.data.append(item_rsp)
        return rsp

    def CreateCartItem(self, request:order_pb2.CartItemRequest, context):
        existed_items = ShoppingCart.select().where(ShoppingCart.user==request.userId, ShoppingCart.goods==request.goodsId)
        if existed_items:
            item = existed_items[0]
            item.nums += request.nums
        else:
            item = ShoppingCart()
            item.user = request.userId
            item.goods = request.goodsId
            item.nums = request.nums
        item.save()
        return order_pb2.ShopCartInfoResponse(id=item.id)

    def UpdateCartItem(self, request, context):
        try:
            item = ShoppingCart.get(ShoppingCart.user == request.userId, ShoppingCart.goods == request.goodsId)
            item.checked = request.checked
            if request.nums:
                item.nums = request.nums
            item.save()
            return empty_pb2()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Shopping cart does not exist")
            return empty_pb2()

    def DeleteCartItem(self, request, context):
        try:
            item = ShoppingCart.get(ShoppingCart.user == request.userId, ShoppingCart.goods == request.goodsId)
            item.delete_instance()
            return empty_pb2.Empty()
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Shopping cart does not exist")
            return empty_pb2.Empty()

    def CreateOrder(self, request, context):
        return super().CreateOrder(request, context)

    def OrderList(self, request, context):
        return super().OrderList(request, context)

    def OrderDetail(self, request, context):
        return super().OrderDetail(request, context)

    def UpdateOrderStatus(self, request, context):
        return super().UpdateOrderStatus(request, context)