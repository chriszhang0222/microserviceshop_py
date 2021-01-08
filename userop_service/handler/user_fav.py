from typing import List

import grpc
from loguru import logger
from peewee import DoesNotExist

from userop_service.models.model import UserFav
from userop_service.proto import userfav_pb2, userfav_pb2_grpc
from google.protobuf import empty_pb2

class UserFavServicer(userfav_pb2_grpc.UserFavServicer):
    @logger.catch
    def GetFavList(self, request, context):
        rsp = userfav_pb2.UserFavListResponse()
        user_favs: List[UserFav] = UserFav.select()
        if request.userId:
            user_favs = user_favs.where(UserFav.user==request.userId)
        if request.goodsId:
            user_favs = user_favs.where(UserFav.goods==request.goodsId)
        rsp.total == user_favs.count()
        for user_fav in user_favs:
            user_fav_rsp = userfav_pb2.UserFavResponse()
            user_fav_rsp.userId = user_fav.user
            user_fav_rsp.goodsId = user_fav.goods
            rsp.data.append(user_fav_rsp)
        return rsp

    @logger.catch
    def AddUserFav(self, request, context):
        user_fav = UserFav()
        user_fav.user = request.userId
        user_fav.goods = request.goodsId
        user_fav.save(force_insert=True)
        return empty_pb2.Empty()

    def DeleteUserFav(self, request, context):
        try:
            user_fav = UserFav.get(UserFav.user == request.userId, UserFav.goods == request.goodsId)
            user_fav.delete_instance(permanently=True)

            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('记录不存在')
            return empty_pb2.Empty()

    def GetUserFavDetail(self, request, context):
        rsp = userfav_pb2.UserFavExist()
        try:
            UserFav.get(UserFav.user==request.userId, UserFav.goods==request.goodsId)
            rsp.exist = True
            return rsp
        except:
            rsp.exist = False
            return rsp