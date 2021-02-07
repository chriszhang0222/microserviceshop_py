import json

import grpc
from inventory_service.proto import inventory_pb2, inventory_pb2_grpc
from inventory_service.model.models import *
from google.protobuf import empty_pb2
from loguru import logger
from common.lock.redis_lock import Lock
from rocketmq.client import ConsumeStatus

def reback_inv(msg):
    #通过ordersn 确定库存归还
    msg_body_str = msg.body.decode("utf-8")
    logger.info(msg_body_str)
    msg_body = json.loads(msg_body_str)
    order_sn = msg_body["orderSn"]
    with settings.DB.atomic() as txn:
        try:
            order_inv = InventoryHistory.get(InventoryHistory.order_sn==order_sn, InventoryHistory.status==1)
            inv_details = json.loads(order_inv.order_inv_detail)
            for item in inv_details:
                goods_id = item["goods_id"]
                num = item["num"]
                Inventory.update(stocks=Inventory.stocks+num).where(Inventory.goods==goods_id).execute()
            order_inv.status = 2
            order_inv.save()
            return ConsumeStatus.CONSUME_SUCCESS
        except DoesNotExist as e:
            return ConsumeStatus.CONSUME_SUCCESS
        except Exception as e:
            txn.rollback()
            return ConsumeStatus.RECONSUME_LATER


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
        inv_history = InventoryHistory(order_sn=request.OrderSn)
        inv_detail = []
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
                    inv_detail.append({
                        "goods_id": item.goodsId,
                        "num": item.num,
                    })
                    goods_inv.stocks -= item.num
                    goods_inv.save()
                lock.release()
        inv_history.order_inv_detail = json.dumps(inv_detail)
        inv_history.save()
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