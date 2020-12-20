from nacos import NacosClient

server_addr = "192.168.0.10:8848"
namespace = "f8bdaf7d-b24e-4080-bcf8-afefc8bcc659"

client = NacosClient(server_addr, namespace=namespace, username="nacos", password="nacos")
data_id = "user-srv.json"
group = "dev"
print(client.get_config(data_id, group))
