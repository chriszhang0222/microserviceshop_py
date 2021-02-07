import json

import grpc
import time
from order_service.proto import order_pb2, order_pb2_grpc
from loguru import logger
from random import Random
from datetime import datetime
from order_service.model.model import *
from google.protobuf import empty_pb2
from common.register import consul
from order_service.settings import settings
from order_service.proto import goods_pb2, goods_pb2_grpc, inventory_pb2, inventory_pb2_grpc
from rocketmq.client import TransactionStatus, TransactionMQProducer, Message, SendStatus

def generate_order_sn(user_id):
    random_ins = Random()
    order_sn = f"{time.strftime('%Y%m%d%H%M%S')}{user_id}{random_ins.randint(10, 99)}"
    return order_sn


local_execute_dict = {}
class OrderService(order_pb2_grpc.OrderServicer):

    @logger.catch
    def CartItemList(self, request: order_pb2.UserInfo, context):
        items = ShoppingCart.select().where(ShoppingCart.user == request.id)
        rsp = order_pb2.CartItemListResponse()
        rsp.total = items.count()
        for item in items:
            item_rsp = order_pb2.ShopCartInfoResponse()
            item_rsp.id = item.id
            item_rsp.userId = item.user
            item_rsp.goodsId = item.goods
            item_rsp.nums = item.nums
            items.checked = item.checked
            rsp.data.append(item_rsp)
        return rsp

    def CreateCartItem(self, request: order_pb2.CartItemRequest, context):
        existed_items = ShoppingCart.select().where(ShoppingCart.user == request.userId,
                                                    ShoppingCart.goods == request.goodsId)
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

    def convert_order_into_response(self, order: OrderInfo) -> order_pb2.OrderInfoResponse:
        order_rsp = order_pb2.OrderInfoResponse()
        order_rsp.id = order.id
        order_rsp.userId = order.user
        order_rsp.orderSn = order.order_sn
        order_rsp.payType = order.pay_type
        order_rsp.status = order.status
        order_rsp.post = order.post
        order_rsp.total = order.order_amount
        order_rsp.address = order.address
        order_rsp.name = order.signer_name
        order_rsp.mobile = order.singer_mobile
        order_rsp.addTime = order.add_time.strftime('%Y-%m-%d %H:%M:%S')
        return order_rsp

    @logger.catch
    def OrderList(self, request, context):
        rsp = order_pb2.OrderListResponse()
        orders = OrderInfo.select()
        if request.userId:
            orders = orders.where(OrderInfo.user == request.userId)
        rsp.total = orders.count()
        per_page_nums = request.pagePerNums if request.pagePerNums else 10
        start = per_page_nums * (request.pages - 1) if request.pages else 0
        orders = orders.limit(per_page_nums).offset(start)
        for order in orders:
            order_rsp = self.convert_order_into_response(order)
            rsp.data.append(order_rsp)
        return rsp

    def OrderDetail(self, request: order_pb2.OrderRequest, context):
        rsp = order_pb2.OrderInfoDetailResponse()
        try:
            if request.userId:
                order: OrderInfo = OrderInfo.get(OrderInfo.id == request.id, OrderInfo.user == request.userId)
            else:
                order: OrderInfo = OrderInfo.get(OrderInfo.id == request.id)
            rsp.orderInfo = self.convert_order_into_response(order)
            order_goods = OrderGoods.select().where(OrderGoods.order == order.id)
            for order_good in order_goods:
                order_goods_rsp = order_pb2.OrderItemResponse()
                order_goods_rsp.id = order_good.id
                order_goods_rsp.goodsId = order_good.goods
                order_goods_rsp.goodsName = order_good.goods_name
                order_goods_rsp.goodsImage = order_good.goods_image
                order_goods_rsp.goodsPrice = float(order_good.goods_price)
                order_goods_rsp.nums = order_good.nums

                rsp.data.append(order_goods_rsp)

            return rsp
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Order does not exist")
            return rsp

    def UpdateOrderStatus(self, request, context):
        OrderInfo.update(status=request.status).where(OrderInfo.order_sn == request.orderSn)
        return empty_pb2.Empty()

    @logger.catch
    def check_callback(self, msg):
        msg_body = json.loads(msg.body.decode("utf-8"))
        order_sn = msg_body["orderSn"]
        orders = OrderInfo.select().where(OrderInfo.order_sn==order_sn)
        if orders:
            return TransactionStatus.ROLLBACK
        else:
            return TransactionStatus.COMMIT

    def local_execute(self, msg, user_args):
        msg_body = json.loads(msg.body.decode("utf-8"))
        order_sn = msg_body["orderSn"]
        with settings.DB.atomic() as txn:
            goods_ids = []
            goods_nums = {}
            order_amount = 0
            order_goods_list = []
            for cart_item in ShoppingCart.select().where(ShoppingCart.user == msg_body["userId"], ShoppingCart.checked == True):
                goods_ids.append(cart_item.goods)
                goods_nums[cart_item.goods] = cart_item.nums
            if not goods_ids:
                local_execute_dict[order_sn]["code"] = grpc.StatusCode.NOT_FOUND
                local_execute_dict[order_sn]["detail"] = "No item in shopping cart"
                return TransactionStatus.ROLLBACK

            # query goods info from goods srv
            register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_POST)
            goods_srv_host, goods_srv_port = register.get_host_port(f'Service == "{settings.Goods_srv_name}"')
            if not goods_srv_host or not goods_srv_port:
                local_execute_dict[order_sn]["code"] = grpc.StatusCode.NOT_FOUND
                local_execute_dict[order_sn]["detail"] = "Goods service not available"
                return TransactionStatus.ROLLBACK

            goods_channel = grpc.insecure_channel(f"{goods_srv_host}:{goods_srv_port}")
            goods_stub = goods_pb2_grpc.GoodsStub(goods_channel)
            goods_sell_info = []
            try:
                goods_rsp = goods_stub.BatchGetGoods(goods_pb2.BatchGoodsIdInfo(id=goods_ids))
                for good in goods_rsp.data:
                    order_amount += good.shopPrice * goods_nums[good.id]
                    order_goods = OrderGoods(goods=good.id, goods_name=good.name, goods_image=good.goodsFrontImage,
                                             goods_price=good.shopPrice, nums=goods_nums[good.id])
                    order_goods_list.append(order_goods)
                    goods_sell_info.append(inventory_pb2.GoodsInvInfo(goodsId=good.id, num=goods_nums[good.id]))
            except grpc.RpcError as e:
                local_execute_dict[order_sn]["code"] = grpc.StatusCode.INTERNAL
                local_execute_dict[order_sn]["detail"] = str(e)
                return TransactionStatus.ROLLBACK
            # prepare half message


            inventory_host, inventory_port = register.get_host_port(f'Service == "{settings.Inventory_srv_name}"')
            if not inventory_host or not inventory_port:
                local_execute_dict[order_sn]["code"] = grpc.StatusCode.INTERNA
                local_execute_dict[order_sn]["detail"] = "Inventory service not available"
                return TransactionStatus.ROLLBACK
            inventory_channel = grpc.insecure_channel(f"{inventory_host}:{inventory_port}")
            inv_stub = inventory_pb2_grpc.InventoryStub(inventory_channel)
            try:
                inv_stub.Sell(inventory_pb2.SellInfo(goodsInfo=goods_sell_info))
            except grpc.RpcError as e:
                local_execute_dict[order_sn]["code"] = grpc.StatusCode.INTERNAL
                local_execute_dict[order_sn]["detail"] = str(e)
                err_code = e.code()
                if err_code == grpc.StatusCode.UNKNOWN or grpc.StatusCode.DEADLINE_EXCEEDED:
                    return TransactionStatus.COMMIT
                else:
                    return TransactionStatus.ROLLBACK

            try:
                order = OrderInfo()
                order.user = msg_body["userId"]
                order.order_sn = order_sn
                order.order_amount = order_amount
                order.address = msg_body["address"]
                order.signer_name = msg_body["name"]
                order.singer_mobile = msg_body["mobile"]
                order.post = msg_body["post"]
                order.save()
                for order_goods in order_goods_list:
                    order_goods.order = order.id
                OrderGoods.bulk_create(order_goods_list)

                ShoppingCart.delete().where(ShoppingCart.user == msg_body["userId"], ShoppingCart.checked == True).execute()
                local_execute_dict[order_sn] = {
                    "code": grpc.StatusCode.OK,
                    "detail": "Create order succeeded",
                    "order": {
                        "id": order.id,
                        "orderSn": order_sn,
                        "total": order.order_amount
                    }
                }
            except Exception as e:
                txn.rollback()
                local_execute_dict[order_sn]["code"] = grpc.StatusCode.INTERNA
                local_execute_dict[order_sn]["detail"] = str(e)
                return TransactionStatus.COMMIT
            return TransactionStatus.ROLLBACK

    def CreateOrder(self, request, context):
        producer = TransactionMQProducer(group_id="mxshop", checker_callback=self.check_callback)
        producer.set_name_server_address(f"{settings.RocketMQ_HOST}:{settings.RocketMQ_PORT}")
        producer.start()
        msg = Message("order_reback")
        msg.set_keys("mxshop")
        msg.set_tags("order")

        order_sn = generate_order_sn(request.userId)
        msg_body = {
            'orderSn': order_sn,
            "userId": request.userId,
            "address": request.address,
            "name": request.name,
            "mobile": request.mobile,
            "post": request.post
        }
        msg.set_body(json.dumps(msg_body))
        ret = producer.send_message_in_transaction(msg, self.local_execute, user_args=None)
        logger.info(f"Send status: {ret.status}, id: {ret.msg_id}")
        if ret.status != SendStatus.OK:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Create order failed")
            return order_pb2.OrderInfoResponse()

        while True:
            if order_sn in local_execute_dict:
                context.set_code(local_execute_dict[order_sn]["code"])
                context.set_details(local_execute_dict[order_sn]["detail"])
                producer.shutdown()
                if local_execute_dict[order_sn]["code"] == grpc.StatusCode.OK:
                    return order_pb2.OrderInfoResponse(id=local_execute_dict[order_sn]["order"]["id"],
                                                       orderSn=order_sn,
                                                       total=local_execute_dict[order_sn]["order"]["total"])
                else:
                    return order_pb2.OrderInfoResponse()
            time.sleep(0.1)


