# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import address_pb2 as address__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class AddressStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetAddressList = channel.unary_unary(
                '/Address/GetAddressList',
                request_serializer=address__pb2.AddressRequest.SerializeToString,
                response_deserializer=address__pb2.AddressListResponse.FromString,
                )
        self.CreateAddress = channel.unary_unary(
                '/Address/CreateAddress',
                request_serializer=address__pb2.AddressRequest.SerializeToString,
                response_deserializer=address__pb2.AddressResponse.FromString,
                )
        self.DeleteAddress = channel.unary_unary(
                '/Address/DeleteAddress',
                request_serializer=address__pb2.AddressRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.UpdateAddress = channel.unary_unary(
                '/Address/UpdateAddress',
                request_serializer=address__pb2.AddressRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class AddressServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetAddressList(self, request, context):
        """查看地址
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateAddress(self, request, context):
        """新增地址
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteAddress(self, request, context):
        """删除地址
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateAddress(self, request, context):
        """修改地址
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AddressServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetAddressList': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAddressList,
                    request_deserializer=address__pb2.AddressRequest.FromString,
                    response_serializer=address__pb2.AddressListResponse.SerializeToString,
            ),
            'CreateAddress': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateAddress,
                    request_deserializer=address__pb2.AddressRequest.FromString,
                    response_serializer=address__pb2.AddressResponse.SerializeToString,
            ),
            'DeleteAddress': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteAddress,
                    request_deserializer=address__pb2.AddressRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'UpdateAddress': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateAddress,
                    request_deserializer=address__pb2.AddressRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Address', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Address(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetAddressList(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Address/GetAddressList',
            address__pb2.AddressRequest.SerializeToString,
            address__pb2.AddressListResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CreateAddress(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Address/CreateAddress',
            address__pb2.AddressRequest.SerializeToString,
            address__pb2.AddressResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeleteAddress(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Address/DeleteAddress',
            address__pb2.AddressRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateAddress(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Address/UpdateAddress',
            address__pb2.AddressRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
