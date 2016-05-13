####################################
## Readable code versus less code ##
####################################

import pika
import threading
import json
import app_client_api as app_api
import callme

from web_server.general_api import general_api as api
from web_server.general_api.general_api import _ACTION_KEYS
from client_model import AppModel


logger = api.__get_logger('app_listener.run')


class BroadcastListener(threading.Thread):
    def __init__(self, nid):
        self.nid = nid
        super(BroadcastListener, self).__init__()
        

    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        channel = connection.channel()
        channel.exchange_declare(exchange=api.EXCHANGE_FOR_ALL,
            type='fanout')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=api.EXCHANGE_FOR_ALL,
            queue=queue_name)
        print(' [*] Waiting for fanout message')

        channel.basic_consume(self._on_message,
                              queue=queue_name,
                              no_ack=True)
        channel.start_consuming()


    def _on_message(self, ch, method, properties, body):
        #try:
        data = json.loads(api.decrypt_msg(
            AppModel.objects(nid=self.nid).scalar('common_key_private').get(), 
            body))     

        ## A node joined the system
        if (data['action'] == _ACTION_KEYS[1]):
            app_api._add_nodes(data['data'], self.nid)

        ## A node left the system
        elif (data['action'] == _ACTION_KEYS[2]):
            app_api._delete_node(data['data']['nid'], self.nid)

        ## common key timeout, needs to be updated
        elif (data['action'] == _ACTION_KEYS[3]):
            if app_api._refresh_common_key(self.nid, 
                data['data']['common_key_private']) == False:
                logger.error("refreshing common key failed")
            else:
                logger.info("common key refresehd...")
                
        #except:
        #    logger.error("error occurred while processing broadcast message")
        #    pass

class MessageListener(threading.Thread):
    def __init__(self, nid):
        self.nid = nid
        super(MessageListener, self).__init__()
        

    def run(self):
        connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                host="localhost",
                port=5672))
        channel = connection.channel()
        channel.exchange_declare(exchange=api.EXCHANGE_END_TO_END,
            type='direct')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=api.EXCHANGE_END_TO_END,
            queue=queue_name,
            routing_key=self.nid)

        print(' [*] Waiting for end-to-end message')

        channel.basic_consume(self._on_message,
                              queue=queue_name,
                              no_ack=True)
        channel.start_consuming()


    def _on_message(self, ch, method, properties, body):
        print "message received!"
        print body

        data = json.loads(api.decrypt_msg(
            AppModel.objects(nid=self.nid).scalar('private_key').get(), 
            body))

        print data    
        server_id = AppModel.objects(nid=self.nid).scalar('master_sid').get()

        ## access to the shared resource has been permitted
        if (data['action'] == _ACTION_KEYS[4]):
            ## TODO: encrypt message
            proxy = callme.Proxy(
                server_id=server_id, 
                amqp_host="localhost",
                amqp_port=5672, 
                timeout=2)

            msg = [
            {
                "by":self.nid, 
                "comment":"first comment haha"
            },
            {
                "by":self.nid, 
                "comment":"second comment haha"
            }]

            proxy.use_server(server_id).add_comment(msg)

        #try:
        #common_key = AppModel.objects(nid=self.nid).scalar('priva').get()
        #data = json.loads(api.decrypt_msg(common_key, body))     
