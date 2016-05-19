####################################
## Readable code versus less code ##
####################################

import pika
import threading
import json

import web_server_api as server_api

from web_server.general_api import general_api as api

logger = api.__get_logger('new_clinet_listener.run')

## define exchange name for broadcasting message
## define handshake queue for handshaking with the new node

 
## listen to new nodes
class NewNodeListener(threading.Thread):
    def __init__(self, sid):
        self.sid = sid
        super(NewNodeListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
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

        ## NOT USED AT THE MOMENT
        channel.queue_bind(
            exchange=api.TOPIC_NEW_NODE,
            queue=queue_name,
            routing_key=api.TOPIC_MASTER_NODES)   

        print(' [*] Waiting for new nodes. To exit press CTRL+C')      
        channel.basic_consume(self._on_message,
                              queue=queue_name,
                              no_ack=False)
        channel.start_consuming()


    def _on_message(self, ch, method, properties, body):
        data = json.loads(body)

        if data['action'] == api._ACTION_KEYS[1]:
            server_api._handshake_to_new_node(data['data'], self.sid)

        if data['action'] == api._ACTION_KEYS[7]:
            logger.info("master node sent something")
            if data['data']['sid'] != self.sid:
                #server_api._broadcast_to_thirdparty(**{'sid':self.sid})
                pass


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

        ## release lock on the shared resource
        if data['action'] == api._ACTION_KEYS[6]:
            server_api._coordinate_acc_to_res(sid=self.sid,
                nid=data['data']['nid'],
                action=api._ACTION_KEYS[6])

