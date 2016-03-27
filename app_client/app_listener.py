import pika
import threading
import json
import app_client_api as app_api

from web_server.general_api import general_api as api
from client_model import AppModel
from server_model import WebServerModel     ## temp

BROADCAST_QUEUE = 'queue_where_it_listen_to_broadcast'
logger = api.__get_logger('app_listener.run')
HOST_ADDR = "192.168.10.102"

def _broadcast_message(a, b, c, data):
    try:
        data = json.loads(api.decrypt_msg(WebServerModel.objects.scalar('private_key_c').get(), data))     ## temp using  WebServerModel 
        action = data.pop('action',[])
        print action
        if (action == 'new_node_added'):
            _data = data.pop('data',[])
            app_api._add_nodes(_data)
        elif (action == 'remove_inactive_client'):
            _data = data.pop('data',[])
            app_api._delete_node(_data.pop('uid',[]))
    except:
        logger.error("error occurred while processing broadcast message")
        pass


class ClientListener(threading.Thread):
    def __init__(self):
        super(ClientListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        channel = connection.channel()
        channel.queue_declare(queue=BROADCAST_QUEUE)  
        channel.basic_consume(_broadcast_message,
                              queue=BROADCAST_QUEUE,
                              no_ack=True)
        channel.start_consuming()

mClientListener = ClientListener()
mClientListener.start()