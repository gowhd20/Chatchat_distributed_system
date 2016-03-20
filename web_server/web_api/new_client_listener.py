import pika
import threading
import json
import callme

from mongo_model import ChildrenModel
from web_server.web_api.web_server_api import mWebServerModel
from web_server.general_api import general_api
from mongoengine import *

WEB_SERVER_NAME = 'chatchat_web_server'
logger = general_api.get_logger('new_clinet_listener.run')

def register_new_client(a, b, c, data):
    data = json.loads(data)
    client_id = data.pop('uid',[])
    client_public_key = data.pop('public_key',[])
    mWebServerModel.update(add_to_set__children=[ChildrenModel(uid=client_id, created_at=data.pop('created_at',[]), public_key=client_public_key)])
    logger.info("client id:"+client_id+" has joined the system, system will notify about server")
    message = json.dumps({'action': 'recognize_gateway', 'parameters': {'gateway_id': WEB_SERVER_NAME, 'gateway_public_key': mWebServerModel.public_key}})
    encrypted_message = general_api.encrypt_msg(client_public_key, message)
    #print encrypted_message

    #3try:
    gateway_proxy = callme.Proxy(server_id=client_id, amqp_host='localhost', timeout=1)
    gateway_proxy.use_server(client_id).execute_command(encrypted_message)
#except:
    #logger.error("failed to reach proxy of app_client")

    #print WebServerModel.objects.scalar('children.id').filter(uid=cid)


class NewClientListener(threading.Thread):
    def __init__(self):
        super(NewClientListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='queue_where_new_client_joins')       
        channel.basic_consume(register_new_client,
                              queue='queue_where_new_client_joins',
                              no_ack=True)
        channel.start_consuming()


mNewClientListener = NewClientListener()
mNewClientListener.start()
