import grpc
import time
from datetime import date
from loguru import logger
from user_service.proto import user_pb2, user_pb2_grpc
from user_service.model.models import User
from peewee import DoesNotExist
from passlib.hash import pbkdf2_sha256
from google.protobuf import empty_pb2


class UserServicer(user_pb2_grpc.UserServicer):

    def convert_user_to_rsp(self, user: User) -> user_pb2.UserInfoResponse:
        user_info_rsp = user_pb2.UserInfoResponse()
        user_info_rsp.id = user.id
        user_info_rsp.password = user.password
        user_info_rsp.mobile = user.mobile
        user_info_rsp.role = user.role
        if user.nick_name:
            user_info_rsp.nickName = user.nick_name
        if user.gender:
            user_info_rsp.gender = user.gender
        if user.birthday:
            user_info_rsp.birthDay = int(time.mktime(user.birthday.timetuple()))
        return user_info_rsp

    @logger.catch
    def CreateUser(self, request: user_pb2.CreateUserInfo, context) -> user_pb2.UserInfoResponse:
        nickname = request.nickName
        password = request.password
        mobile = request.mobile
        try:
            user = User.get(User.mobile == mobile)
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("User exist")
            return user_pb2.UserInfoResponse()
        except DoesNotExist:
            pass
        user = User()
        user.nick_name = nickname
        user.mobile = mobile
        user.password = pbkdf2_sha256.hash(password)
        user.save()
        return self.convert_user_to_rsp(user)

    @logger.catch
    def UpdateUser(self, request: user_pb2.UpdateUserInfo, context):
        try:
            user = User.get(User.id == request.id)
            if request.nickName is not None and request.nickName != '':
                user.nick_name = request.nickName
            if request.gender is not None and request.gender != '':
                user.gender = request.gender
            if request.birthday is not None and request.birthday != 0:
                user.birthday = date.fromtimestamp(request.birthday)
            user.save()
            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User does not exist")
            return empty_pb2.Empty()


    @logger.catch
    def GetUserList(self, request: user_pb2.PageInfo, context):
        users = User.select()
        rsp = user_pb2.UserListResponse()
        rsp.total = users.count()
        start = 0
        per_page_numbers = 10
        if request.pSize:
            per_page_numbers = request.pSize
        if request.pn:
            start = per_page_numbers * (request.pn - 1)
        users = users.limit(per_page_numbers).offset(start)

        for user in users:
            user_info_rsp = self.convert_user_to_rsp(user)
            rsp.data.append(user_info_rsp)
        return rsp

    @logger.catch
    def GetUserByMobile(self, request: user_pb2.MobileRequest, context):
        try:
            user = User.get(User.mobile == request.mobile)
            user_info_rsp = self.convert_user_to_rsp(user)
            return user_info_rsp
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User does not exist")
            return user_pb2.UserInfoResponse()

    @logger.catch
    def GetUserById(self, request: user_pb2.IdRequest, context):
        try:
            user = User.get(User.id == request.id)
            user_info_rsp = self.convert_user_to_rsp(user)
            return user_info_rsp

        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User does not exist")
            return user_pb2.UserInfoResponse()
