import grpc
from data_service.proto import data_pb2, data_pb2_grpc


class DataClient:
    def __init__(self,ip, port):
        channel = grpc.insecure_channel(f"{ip}:{port}")
        self.data_stub = data_pb2_grpc.DataServiceStub(channel)

    def GetData(self):
        rsp = self.data_stub.GetData(data_pb2.DataRequest(
            id=2,name="hello"
        ))
        print(rsp.code)
        print(rsp.content)


a = DataClient("192.168.0.14", "50099")
a.GetData()