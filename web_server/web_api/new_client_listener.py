import pika
import threading
import json
import callme
import web_server_api as web_api

from server_model import WebServerModel
from web_server.general_api import general_api as api
from mongoengine import *

logger = api.__get_logger('new_clinet_listener.run')
BROADCAST_QUEUE = "queue_where_it_listen_to_broadcast"
HOST_ADDR = "192.168.10.102"

def _register_new_client(a, b, c, data):
    data = json.loads(data)
    client_id = data.pop('uid',[])
    client_created_at = data.pop('created_at',[])
    client_public_key = data.pop('public_key',[])

    ## add client info into children document 
    web_api._add_children(client_id, client_created_at, client_public_key)
    logger.info("client id:"+client_id+" has joined the system")

    message = json.dumps({
        'action':'web_server_info', 
        'data':{
            'server_id': WebServerModel.objects.scalar('uid').get(), 
            'server_public_key': WebServerModel.objects.scalar('public_key').get(),
            'private_key_c': WebServerModel.objects.scalar('private_key_c').get()
            }
        })
    encrypted_message = api.encrypt_msg(client_public_key, message)

    childs = WebServerModel.objects.get().children
    message = {}
    for child in childs:
        if not message:
            message = {
                'action':'new_node_added',
                'data':[{
                    'uid':child.uid,
                    'public_key':child.public_key
                }]
            }
        else:
            message['data'].append({
                'uid':child.uid,
                'public_key':child.public_key
                })

    ## broadcast of a new client to all nodes
    web_api._broadcast_to_nodes(BROADCAST_QUEUE, 
        api.encrypt_msg(WebServerModel.objects.scalar('public_key_c').get(),
            json.dumps(message)))

    proxy = callme.Proxy(server_id=client_id, amqp_host="localhost", timeout=1)
    proxy.use_server(client_id).execute_command(encrypted_message)
 

class NewClientListener(threading.Thread):
    def __init__(self):
        super(NewClientListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost",port=5672))
        channel = connection.channel()
        channel.queue_declare(queue='queue_where_new_client_joins')     
        channel.basic_consume(_register_new_client,
                              queue='queue_where_new_client_joins',
                              no_ack=True)
        channel.start_consuming()


mNewClientListener = NewClientListener()
mNewClientListener.start()
