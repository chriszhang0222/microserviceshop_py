from inventory_service.proto import inventory_pb2, inventory_pb2_grpc
from inventory_service.model.models import *
from google.protobuf import empty_pb2


class InventoryService(inventory_pb2_grpc.InventoryServicer):
    def SetInv(self, request, context):
        return super().SetInv(request, context)

    def InvDetail(self, request, context):
        return super().InvDetail(request, context)

    def Sell(self, request, context):
        return super().Sell(request, context)

    def Reback(self, request, context):
        return super().Reback(request, context)