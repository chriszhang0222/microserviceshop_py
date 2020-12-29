import json

import grpc
import time
from goods_service.proto import goods_pb2, goods_pb2_grpc
from goods_service.model.models import *
from google.protobuf import empty_pb2
from loguru import logger


class GoodsServices(goods_pb2_grpc.GoodsServicer):
    def category_model_to_dic(self, category: Category) -> dict:
        res = {
            "id": category.id,
            "name": category.name,
            "level": category.level,
            "parent": category.parent_category_id,
            "is_tab": category.is_tab
        }
        return res

    def convert_model_to_message(self, goods: BaseModel) -> goods_pb2.GoodsInfoResponse:
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
                        c2.select(c2.id).where(c2.parent_category_id == request.topCategory)
                    ))
                    for category in categorys:
                        ids.append(category.id)
                elif level == 2:
                    categorys = Category.select().where(Category.parent_category_id == request.topCategory)
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
            category = Category.get(Category.id == request.categoryId)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Category does not exist")
            return goods_pb2.GoodsInfoResponse()
        try:
            brand = Brands.get(Brands.id == request.brandId)
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
            goods: Goods = Goods.get(Goods.id == request.id)
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

    @logger.catch
    def GetAllCategorysList(self, request, context):
        rsp = goods_pb2.CategoryListResponse()
        categories = Category.select()
        rsp.total = categories.count()
        level1, level2, level3 = [], [], []
        for category in categories:
            category_rsp = goods_pb2.CategoryInfoResponse()
            category_rsp.id = category.id
            category_rsp.name = category.name
            if category.parent_category_id:
                category_rsp.parentCategory = category.parent_category_id
            category_rsp.level = category.level
            category_rsp.isTab = category.is_tab
            rsp.data.append(category_rsp)
            if category.level == 1:
                level1.append(self.category_model_to_dic(category))
            elif category.level == 2:
                level2.append(self.category_model_to_dic(category))
            elif category.level == 3:
                level3.append(self.category_model_to_dic(category))

        for data3 in level3:
            for data2 in level2:
                if data3["parent"] == data2["id"]:
                    if "sub_category" not in data2:
                        data2["sub_category"] = [data3]
                    else:
                        data2["sub_category"].append(data3)
        for data2 in level2:
            for data1 in level1:
                if data2["parent"] == data1["id"]:
                    if "sub_category" not in data1:
                        data1["sub_category"] = [data2]
                    else:
                        data1["sub_category"].append(data2)
        rsp.jsonData = json.dumps(level1)
        return rsp

    def GetSubCategory(self, request, context):
        category_list_rsp = goods_pb2.SubCategoryListResponse()

        try:
            category_info = Category.get(Category.id == request.id)
            category_list_rsp.info.id = category_info.id
            category_list_rsp.info.name = category_info.name
            category_list_rsp.info.level = category_info.level
            category_list_rsp.info.isTab = category_info.is_tab
            if category_info.parent_category:
                category_list_rsp.info.parentCategory = category_info.parent_category_id
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Category does not exist')
            return goods_pb2.SubCategoryListResponse()

        categorys = Category.select().where(Category.parent_category == request.id)
        category_list_rsp.total = categorys.count()
        for category in categorys:
            category_rsp = goods_pb2.CategoryInfoResponse()
            category_rsp.id = category.id
            category_rsp.name = category.name
            if category_info.parent_category:
                category_rsp.parentCategory = category_info.parent_category_id
            category_rsp.level = category.level
            category_rsp.isTab = category.is_tab

            category_list_rsp.subCategorys.append(category_rsp)

        return category_list_rsp

    def CreateCategory(self, request, context):
        try:
            category = Category()
            category.name = request.name
            if request.level != 1:
                category.parent_category = request.parentCategory
            category.level = request.level
            category.is_tab = request.isTab
            category.save()

            category_rsp = goods_pb2.CategoryInfoResponse()
            category_rsp.id = category.id
            category_rsp.name = category.name
            if category.parent_category:
                category_rsp.parentCategory = category.parent_category.id
            category_rsp.level = category.level
            category_rsp.isTab = category.is_tab
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return goods_pb2.CategoryInfoResponse()

        return category_rsp

    def DeleteCategory(self, request, context):
        try:
            category = Category.get(request.id)
            category.delete_instance()

            # TODO 删除响应的category下的商品
            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Does not exist')
            return empty_pb2.Empty()

    def UpdateCategory(self, request, context):
        try:
            category = Category.get(request.id)
            if request.name:
                category.name = request.name
            if request.parentCategory:
                category.parent_category = request.parentCategory
            if request.level:
                category.level = request.level
            if request.isTab:
                category.is_tab = request.isTab
            category.save()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Does not exist')
            return empty_pb2.Empty()

    @logger.catch
    def BannerList(self, request: empty_pb2.Empty, context):
        # 获取分类列表
        rsp = goods_pb2.BannerListResponse()
        banners = Banner.select()

        rsp.total = banners.count()
        for banner in banners:
            banner_rsp = goods_pb2.BannerResponse()

            banner_rsp.id = banner.id
            banner_rsp.image = banner.image
            banner_rsp.index = banner.index
            banner_rsp.url = banner.url

            rsp.data.append(banner_rsp)

        return rsp

    @logger.catch
    def CreateBanner(self, request: goods_pb2.BannerRequest, context):
        banner = Banner()

        banner.image = request.image
        banner.index = request.index
        banner.url = request.url
        banner.save()

        banner_rsp = goods_pb2.BannerResponse()
        banner_rsp.id = banner.id
        banner_rsp.image = banner.image
        banner_rsp.url = banner.url

        return banner_rsp

    @logger.catch
    def DeleteBanner(self, request: goods_pb2.BannerRequest, context):
        try:
            banner = Banner.get(request.id)
            banner.delete_instance()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Banner does not exist')
            return empty_pb2.Empty()

    @logger.catch
    def UpdateBanner(self, request: goods_pb2.BannerRequest, context):
        try:
            banner = Banner.get(request.id)
            if request.image:
                banner.image = request.image
            if request.index:
                banner.index = request.index
            if request.url:
                banner.url = request.url

            banner.save()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Banner does not exist')
            return empty_pb2.Empty()

    # 品牌相关的接口

    @logger.catch
    def BrandList(self, request: empty_pb2.Empty, context):
        # 获取品牌列表
        start, per_page = 0, 10
        if request.pagePerNums:
            per_page = request.pagePerNums
        if request.pages:
            start = per_page * (request.pages-1)
        rsp = goods_pb2.BrandListResponse()
        brands = Brands.select()

        rsp.total = brands.count()
        brands = brands.limit(per_page).offset(start)
        for brand in brands:
            brand_rsp = goods_pb2.BrandInfoResponse()

            brand_rsp.id = brand.id
            brand_rsp.name = brand.name
            brand_rsp.logo = brand.logo

            rsp.data.append(brand_rsp)

        return rsp

    @logger.catch
    def CreateBrand(self, request: goods_pb2.BrandRequest, context):
        brands = Brands.select().where(Brands.name == request.name)
        if brands:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details('Brand Already Exists')
            return goods_pb2.BrandInfoResponse()

        brand = Brands()

        brand.name = request.name
        brand.logo = request.logo

        brand.save()

        rsp = goods_pb2.BrandInfoResponse()
        rsp.id = brand.id
        rsp.name = brand.name
        rsp.logo = brand.logo

        return rsp

    @logger.catch
    def DeleteBrand(self, request: goods_pb2.BrandRequest, context):
        try:
            brand = Brands.get(request.id)
            brand.delete_instance()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record does not exist')
            return empty_pb2.Empty()

    @logger.catch
    def UpdateBrand(self, request: goods_pb2.BrandRequest, context):
        try:
            brand = Brands.get(request.id)
            if request.name:
                brand.name = request.name
            if request.logo:
                brand.logo = request.logo

            brand.save()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record does not exist')
            return empty_pb2.Empty()

    @logger.catch
    def CategoryBrandList(self, request: empty_pb2.Empty, context):
        # 获取品牌分类列表
        rsp = goods_pb2.CategoryBrandListResponse()
        category_brands = GoodsCategoryBrand.select()

        # 分页
        start = 0
        per_page_nums = 10
        if request.pagePerNums:
            per_page_nums = request.PagePerNums
        if request.pages:
            start = per_page_nums * (request.pages - 1)

        category_brands = category_brands.limit(per_page_nums).offset(start)

        rsp.total = category_brands.count()
        for category_brand in category_brands:
            category_brand_rsp = goods_pb2.CategoryBrandResponse()

            category_brand_rsp.id = category_brand.id
            category_brand_rsp.brand.id = category_brand.brand.id
            category_brand_rsp.brand.name = category_brand.brand.name
            category_brand_rsp.brand.logo = category_brand.brand.logo

            category_brand_rsp.category.id = category_brand.category.id
            category_brand_rsp.category.name = category_brand.category.name
            category_brand_rsp.category.parentCategory = category_brand.category.parent_category_id
            category_brand_rsp.category.level = category_brand.category.level
            category_brand_rsp.category.isTab = category_brand.category.is_tab

            rsp.data.append(category_brand_rsp)
        return rsp

    @logger.catch
    def GetCategoryBrandList(self, request, context):
        # 获取某一个分类的所有品牌
        rsp = goods_pb2.BrandListResponse()
        try:
            category = Category.get(Category.id == request.id)
            category_brands = GoodsCategoryBrand.select().where(GoodsCategoryBrand.category == category)
            rsp.total = category_brands.count()
            for category_brand in category_brands:
                brand_rsp = goods_pb2.BrandInfoResponse()
                brand_rsp.id = category_brand.brand.id
                brand_rsp.name = category_brand.brand.name
                brand_rsp.logo = category_brand.brand.logo

                rsp.data.append(brand_rsp)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record does not exist')
            return rsp

        return rsp

    @logger.catch
    def CreateCategoryBrand(self, request: goods_pb2.CategoryBrandRequest, context):
        category_brand = GoodsCategoryBrand()

        try:
            brand = Brands.get(request.brandId)
            category_brand.brand = brand
            category = Category.get(request.categoryId)
            category_brand.category = category
            category_brand.save()

            rsp = goods_pb2.CategoryBrandResponse()
            rsp.id = category_brand.id  # 是另外一种思路

            return rsp
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record does not exist')
            return goods_pb2.CategoryBrandResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal Server Error')
            return goods_pb2.CategoryBrandResponse()

    @logger.catch
    def DeleteCategoryBrand(self, request: goods_pb2.CategoryBrandRequest, context):
        try:
            category_brand = GoodsCategoryBrand.get(request.id)
            category_brand.delete_instance()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record does not exist')
            return empty_pb2.Empty()

    @logger.catch
    def UpdateCategoryBrand(self, request: goods_pb2.CategoryBrandRequest, context):
        try:
            category_brand = GoodsCategoryBrand.get(request.id)
            brand = Brands.get(request.brandId)
            category_brand.brand = brand
            category = Category.get(request.categoryId)
            category_brand.category = category
            category_brand.save()

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record does not exist')
            return empty_pb2.Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return empty_pb2.Empty()




