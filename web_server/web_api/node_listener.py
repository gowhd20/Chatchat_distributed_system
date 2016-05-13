####################################
## Readable code versus less code ##
####################################

import pika
import threading
import json
#import callme
import web_server_api as server_api

#from server_model import WebServerModel
from web_server.general_api import general_api as api
from web_server.general_api.general_api import _ACTION_KEYS
#from mongoengine import *

logger = api.__get_logger('new_clinet_listener.run')

## define exchange name for broadcasting message
## define handshake queue for handshaking with the new node

HOST_ADDR = "192.168.10.102"

 
## listen to new nodes
class NewNodeListener(threading.Thread):
    def __init__(self, sid):
        self.sid = sid
        super(NewNodeListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host="localhost",
            port=5672))
        channel = connection.channel()
        channel.exchange_declare(
            exchange=api.TOPIC_NEW_NODE,
            type='topic')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(
            exchange=api.TOPIC_NEW_NODE,
            queue=queue_name,
            routing_key=api.MN_RKEY+str(api.ID_OF_MN))     ## indicates master server number

        print(' [*] Waiting for new nodes. To exit press CTRL+C')      
        channel.basic_consume(self._on_message,
                              queue=queue_name,
                              no_ack=True)
        channel.start_consuming()


    def _on_message(self, ch, method, properties, body):
        data = json.loads(body)
        print data
        ch.basic_ack(delivery_tag = method.delivery_tag)
        if data['action'] == _ACTION_KEYS[1]:
            server_api._handshake_to_new_node(data['data'], self.sid)

        #elif data['action'] == _ACTION_KEYS[4]:
        #    if server_api._coordinate_acc_to_res(data['data']['nid']):
        #        server_api._broadcast_to_nodes(EXCHANGE_FOR_ALL, )


class NodeMessageListener(threading.Thread):
    def __init__(self, sid):
        self.sid = sid
        super(NodeMessageListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                host="localhost",
                port=5672))
        channel = connection.channel()
        channel.exchange_declare(
            exchange=api.EXCHANGE_END_TO_END,
            type='direct')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(
            exchange=api.EXCHANGE_END_TO_END,
            queue=queue_name,
            routing_key=self.sid)

        print(' [*] Waiting for end-to-end message')

        channel.basic_consume(self._on_message,
                              queue=queue_name,
                              no_ack=True)
        channel.start_consuming()


    def _on_message(self, ch, method, properties, body):
        data = json.loads(body)
        print data

        #if data['action'] == _ACTION_KEYS[1]:
        #    server_api._handshake_to_new_node(data['data'])

        #elif data['action'] == _ACTION_KEYS[4]:
        #    if server_api._coordinate_acc_to_res(data['data']['nid']):
        #        server_api._broadcast_to_nodes(EXCHANGE_FOR_ALL, )
