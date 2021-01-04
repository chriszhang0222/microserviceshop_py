from order_service.proto import order_pb2, order_pb2_grpc


class OrderService(order_pb2_grpc.OrderServicer):
    def CartItemList(self, request, context):
        return super().CartItemList(request, context)

    def CreateCartItem(self, request, context):
        return super().CreateCartItem(request, context)

    def UpdateCartItem(self, request, context):
        return super().UpdateCartItem(request, context)

    def DeleteCartItem(self, request, context):
        return super().DeleteCartItem(request, context)

    def CreateOrder(self, request, context):
        return super().CreateOrder(request, context)

    def OrderList(self, request, context):
        return super().OrderList(request, context)

    def OrderDetail(self, request, context):
        return super().OrderDetail(request, context)

    def UpdateOrderStatus(self, request, context):
        return super().UpdateOrderStatus(request, context)