import grpc
import time
from goods_service.proto import goods_pb2, goods_pb2_grpc
from goods_service.model.models import *
from google.protobuf import empty_pb2
from loguru import logger


class GoodsServices(goods_pb2_grpc.GoodsServicer):
    def convert_model_to_message(self, goods:BaseModel) -> goods_pb2.GoodsInfoResponse:
        info_rsp = goods_pb2.GoodsInfoResponse()
        info_rsp.id = goods.id
        info_rsp.categoryId = goods.category_id
        info_rsp.name = goods.name
        info_rsp.goodsSn = goods.goods_sn
        info_rsp.clickNum = goods.click_num
        info_rsp.soldNum = goods.sold_num
        info_rsp.favNum = goods.fav_num
        info_rsp.marketPrice = goods.market_price
        info_rsp.shopPrice = goods.shop_price
        info_rsp.goodsBrief = goods.goods_brief
        info_rsp.shipFree = goods.ship_free
        info_rsp.goodsFrontImage = goods.goods_front_image
        info_rsp.isNew = goods.is_new
        info_rsp.descImages.extend(goods.desc_images)
        info_rsp.images.extend(goods.desc_images)
        info_rsp.isHot = goods.is_hot
        info_rsp.onSale = goods.on_sale

        info_rsp.category.id = goods.category.id
        info_rsp.category.name = goods.category.name

        info_rsp.brand.id = goods.brand.id
        info_rsp.brand.name = goods.brand.name
        info_rsp.brand.logo = goods.brand.logo

        return info_rsp

    @logger.catch
    def GoodsList(self, request: goods_pb2.GoodsFilterRequest, context) -> goods_pb2.GoodsListResponse:
        rsp = goods_pb2.GoodsListResponse()
        goods: BaseModel = Goods.select()
        if request.keyWords:
            goods = goods.where(Goods.name.contains(request.keyWords))
        if request.isHot:
            goods = goods.filter(Goods.is_hot == True)
        if request.isNew:
            goods = goods.filter(Goods.is_new == True)
        if request.priceMin:
            goods = goods.filter(Goods.shop_price >= request.priceMin)
        if request.priceMax:
            goods = goods.filter(Goods.shop_price <= request.priceMax)
        if request.brand:
            goods = goods.filter(Goods.brand_id == request.brand)
        if request.topCategory:
            try:
                ids = []
                category = Category.get(Category.id == request.topCategory)
                level = category.level
                if level == 1:
                    c2 = Category.alias()
                    categorys = Category.select().where(Category.parent_category_id.in_(
                        c2.select(c2.id).where(c2.parent_category_id==request.topCategory)
                    ))
                    for category in categorys:
                        ids.append(category.id)
                elif level == 2:
                    categorys = Category.select().where(Category.parent_category_id==request.topCategory)
                    for category in categorys:
                        ids.append(category.id)
                elif level == 3:
                    ids.append(request.topCategory)
                goods = goods.where(Goods.category_id.in_(ids))
            except Exception as e:
                pass
        start, per_page_nums = 0, 10
        if request.pagePerNums:
            per_page_nums = request.pagePerNums
        if request.pages:
            start = per_page_nums * (request.pages - 1)
        rsp.total = goods.count()
        goods = goods.limit(per_page_nums).offset(start)
        for good in goods:
            rsp.data.append(self.convert_model_to_message(good))
        return rsp

    @logger.catch
    def GetGoodsDetail(self, request: goods_pb2.GoodInfoRequest, context):
        try:
            goods = Goods.get(Goods.id == request.id)
            goods.click_num += 1
            goods.save()
            return self.convert_model_to_message(goods)
        except:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Goods Does not exist")
            return goods_pb2.GoodsInfoResponse()

    @logger.catch
    def BatchGetGoods(self, request: goods_pb2.BatchGoodsIdInfo, context) -> goods_pb2.GoodsListResponse:
        rsp = goods_pb2.GoodsListResponse()
        ids = request.id
        goods = Goods.where(Goods.id.in_(ids))
        rsp.total = goods.count()
        for good in goods:
            rsp.append(self.convert_model_to_message(good))
        return rsp

    @logger.catch
    def CreateGoods(self, request: goods_pb2.CreateGoodsInfo, context) -> goods_pb2.GoodsInfoResponse:
        try:
            category = Category.get(Category.id==request.categoryId)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Category does not exist")
            return goods_pb2.GoodsInfoResponse()
        try:
            brand = Brands.get(Brands.id==request.brandId)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Brand does not exist")
            return goods_pb2.GoodsInfoResponse()
        goods = Goods()
        goods.brand = brand
        goods.category = category
        goods.name = request.name
        goods.goods_sn = request.goodsSn
        goods.market_price = request.marketPrice
        goods.shop_price = request.shopPrice
        goods.goods_brief = request.goodsBrief
        goods.ship_free = request.shipFree
        goods.images = list(request.images)
        goods.desc_images = list(request.descImages)
        goods.goods_front_image = request.goodsFrontImage
        goods.is_new = request.isNew
        goods.is_hot = request.isHot
        goods.on_sale = request.onSale
        goods.save()
        return self.convert_model_to_message(goods)


    @logger.catch
    def DeleteGoods(self, request: goods_pb2.DeleteGoodsInfo, context):
        try:
            goods:Goods = Goods.get(Goods.id == request.id)
            goods.delete_instance()
            return empty_pb2.Empty()
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Good does not exist")
            return empty_pb2.Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return empty_pb2.Empty()

    @logger.catch
    def UpdateGoods(self, request: goods_pb2.CreateGoodsInfo, context):
        if not request.id:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Empty Goods id")
            return empty_pb2.Empty()
        category, brand = None, None
        if request.categoryId:
            try:
                category = Category.get(Category.id == request.categoryId)
            except DoesNotExist as e:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Category does not exist")
                return goods_pb2.GoodsInfoResponse()
        if request.brandId:
            try:
                brand = Brands.get(Brands.id == request.brandId)
            except DoesNotExist as e:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Brand does not exist")
                return goods_pb2.GoodsInfoResponse()

        try:
            goods = Goods.get(Goods.id == request.id)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Goods does not exist")
            return goods_pb2.GoodsInfoResponse()

        if brand:
            goods.brand = brand
        if category:
            goods.category = category
        goods.name = request.name
        goods.goods_sn = request.goodsSn
        goods.market_price = request.marketPrice
        goods.shop_price = request.shopPrice
        goods.goods_brief = request.goodsBrief
        goods.ship_free = request.shipFree
        goods.images = list(request.images)
        goods.desc_images = list(request.descImages)
        goods.goods_front_image = request.goodsFrontImage
        goods.is_new = request.isNew
        goods.is_hot = request.isHot
        goods.on_sale = request.onSale

        goods.save()
        return self.convert_model_to_message(goods)








