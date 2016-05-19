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
from client_model import AppModel, CommentReplicaModel


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
        print "fanout message"
        data = json.loads(api.decrypt_msg(
            AppModel.objects(nid=self.nid).scalar('common_key_private').get(), 
            body))     
        #logger.info(data['action'])
        ## A node joined the system
        if (data['action'] == _ACTION_KEYS[1]):
            app_api._add_nodes(data['data'], self.nid)

        ## delete nodes left the system
        elif (data['action'] == _ACTION_KEYS[2]):
            if not isinstance(data['data'], list):
                app_api._delete_nodes(data['data']['nid'], self.nid)
            else:
                app_api._delete_nodes(data['data'], self.nid)

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

        data = json.loads(api.decrypt_msg(
            AppModel.objects(nid=self.nid).scalar('private_key').get(), 
            body))

        print data  
        server_id = AppModel.objects(nid=self.nid).scalar('master_sid').get()

        ## access to the shared resource has been permitted
        if (data['action'] == _ACTION_KEYS[8]):
            if server_id == data['by']:     #   for minimum integrity
                #   this data format is to save contents by 'add_comments' function
                #   send all data that is locally stored then it will be filtered to store to
                #   the shared resource inside 'add_comments' function
                data = {
                    'permission':True,      #   this action would be only triggered with master server's permission
                    'nid':self.nid,
                    'sid':data['by'],
                    'content':map(lambda x:{
                            'by':x.by,
                            'created_at':x.timestamp,
                            'comment':x.comment,
                            'session_id':x.session_id
                        }, CommentReplicaModel.objects.all())
                }

                app_api.add_comments(**data)  
