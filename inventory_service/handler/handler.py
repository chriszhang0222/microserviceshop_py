import grpc
from inventory_service.proto import inventory_pb2, inventory_pb2_grpc
from inventory_service.model.models import *
from google.protobuf import empty_pb2
from loguru import logger


class InventoryService(inventory_pb2_grpc.InventoryServicer):
    @logger.catch
    def SetInv(self, request: inventory_pb2.GoodsInvInfo, context):
        force_insert = False
        goods_id = request.goodsId
        num = request.num
        invs = Inventory.select().where(Inventory.goods==goods_id)
        if not invs:
            inv = Inventory()
            inv.goods = goods_id
            force_insert = True
        else:
            inv = invs[0]
        inv.stocks = num
        inv.save(force_insert=force_insert)
        return empty_pb2.Empty()

    @logger.catch
    def InvDetail(self, request, context):
        try:
            inv = Inventory.get(Inventory.goods==request.goodsId)
            return inventory_pb2.GoodsInvInfo(goodsId=inv.goods, num=inv.stocks)
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Inventory not found")
            return inventory_pb2.GoodsInvInfo()

    def Sell(self, request, context):
        return super().Sell(request, context)

    def Reback(self, request, context):
        return super().Reback(request, context)