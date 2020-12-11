import grpc
from user_service.proto import user_pb2, user_pb2_grpc


class UserTest:
    def __init__(self):
        channel = grpc.insecure_channel("127.0.0.1:50058")
        self.stub = user_pb2_grpc.UserStub(channel)

    def user_list(self):
        rsp :user_pb2.UserListResponse = self.stub.GetUserList(user_pb2.PageInfo())
        print(rsp.total)
        for user in rsp.data:
            print(user.mobile, user.id, user.birthDay)

    def user_by_id(self):
        rsp : user_pb2.UserInfoResponse = self.stub.GetUserById(user_pb2.IdRequest(id=1))
        print(rsp.password)

    def user_by_mobile(self):
        pass

    def create_user(self):
        rsp : user_pb2.UserInfoResponse = self.stub.CreateUser(user_pb2.CreateUserInfo(
            nickName="ok",
            mobile="12222222",
            password="123456"
        ))
        print(rsp.id)


if __name__ == "__main__":
    user = UserTest()
    user.create_user()
