import consul
import requests
from loguru import logger


class BaseServer:
    USER_SERVICE_HOST = None
    USER_SERVICE_PORT = None
    CONSUL_HOST = None
    CONSUL_PORT = None
    SERVICE_NAME = None
    SERVICE_ID = None
    server = None
    consul = None

    def read_config(self):
        pass

    def serve(self):
        pass

    def register(self):
        self.consul = consul.Consul(host=self.CONSUL_HOST, port=self.CONSUL_PORT)
        check = {
            "GRPC": f"{self.USER_SERVICE_HOST}:{self.USER_SERVICE_PORT}",
            "GRPCUseTLS": False,
            "Timeout": "5s",
            "Interval": "5s",
            "DeregisterCriticalServiceAfter": "15s"
        }
        rsp: bool = self.consul.agent.service.register(name=self.SERVICE_NAME, service_id=self.SERVICE_ID,
                                                       address=self.USER_SERVICE_HOST, port=self.USER_SERVICE_PORT,
                                                       tags=["mxshop"], check=check)
        if rsp:
            logger.info('Registered at consul {}:{}'.format(self.CONSUL_HOST, self.CONSUL_PORT))
        else:
            raise Exception('Failed to registered at consul ' + f"{self.CONSUL_HOST}:{self.CONSUL_PORT}")

    def unregister(self):
        if self.consul is not None:
            logger.info('Unregister from consul {}:{}'.format(self.CONSUL_HOST, self.CONSUL_PORT))
            self.consul.agent.service.deregister(self.SERVICE_ID)

    def get_all_service(self):
        return self.consul.Agent.services()

    def filter_service(self, filter: str):
        url = f"{self.CONSUL_HOST}:{self.CONSUL_PORT}/v1/agent/services"
        params = {
            "filter": f'Service=="{filter}"'
        }
        return requests.get(url, params=params).json()
