import grpc
import time
from datetime import date
from user_service.proto import user_pb2, user_pb2_grpc
from user_service.model.models import User


class UserServicer(user_pb2_grpc.UserServicer):
    def GetUserList(self, request: user_pb2.PageInfo, context):
        users = User.select()
        rsp = user_pb2.UserListResponse()
        rsp.total = users.count()
        start = 0
        page = 1
        per_page_numbers = 10
        if request.pSize:
            per_page_numbers = request.pSize
        if request.pn:
            start = per_page_numbers * (request.pn - 1)
        users = users.limit(per_page_numbers).offset(start)

        for user in users:
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
            rsp.data.append(user_info_rsp)
        return rsp


