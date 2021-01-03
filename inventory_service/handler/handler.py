import grpc
from inventory_service.proto import inventory_pb2, inventory_pb2_grpc
from inventory_service.model.models import *
from google.protobuf import empty_pb2
from loguru import logger
from common.lock.redis_lock import Lock


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

    @logger.catch
    def Sell(self, request: inventory_pb2.SellInfo, context):
        with settings.DB.atomic() as txn:
            for item in request.goodsInfo:
                lock = Lock(settings.Redis_client, f"lock:goods_{item.goodsId}", auto_renewal=True, expire=10)
                lock.acquire()
                try:
                    goods_inv = Inventory.get(Inventory.goods==item.goodsId)
                except DoesNotExist:
                    txn.rollback()
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("Not found")
                    return empty_pb2.Empty()
                if goods_inv.stocks < item.num:
                    txn.rollback()
                    context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                    context.set_details(f"Inventory is not enough for goods:{item.goodsId}")
                    return empty_pb2.Empty()
                else:
                    goods_inv.stocks -= item.num
                    goods_inv.save()
                lock.release()
        return empty_pb2.Empty()

    @logger.catch
    def Reback(self, request, context):
        with settings.DB.atomic() as txn:
            for item in request.goodsInfo:
                lock = Lock(settings.Redis_client, f"lock:goods_{item.goodsId}", auto_renewal=True, expire=10)
                lock.acquire()
                try:
                    goods_inv = Inventory.get(Inventory.goods == item.goodsId)
                except DoesNotExist as e:
                    txn.rollback()  # 事务回滚
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    return empty_pb2.Empty()
                goods_inv.stocks += item.num
                goods_inv.save()
                lock.release()
            return empty_pb2.Empty()