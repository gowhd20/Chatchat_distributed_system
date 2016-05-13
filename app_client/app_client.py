####################################
## Readable code versus less code ##
####################################

import threading
import pika
import json
import sys
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

import app_client_api as app_api
import redis

from web_server.general_api import general_api as api
from web_server.general_api.general_api import _ACTION_KEYS
from mongoengine import *
from client_model import AppModel
from app_core import Node
from server_listener import BroadcastListener, MessageListener

MSG_FROM_NODES = "msg_from_nodes"
## if this file is directly ran by python
if __name__ == "__main__":

    connect('chatchat')

    private_key = api.generate_private_key()
    m_AppModel = AppModel(
        public_key=api.generate_public_key(private_key).exportKey().decode('utf-8'), 
        nid=str(api.__uuid_generator_1()), 
        private_key=private_key.exportKey().decode('utf-8'))

    ## this will execute document.insert()
    m_AppModel.save()

    # node instance
    mNode = Node(m_AppModel.nid, m_AppModel.private_key)
    mNode.start()

    # listener for receiving broadcasted msg from the master server
    mBroadcastListener = BroadcastListener(m_AppModel.nid)
    mBroadcastListener.start()

    mMessageListener = MessageListener(m_AppModel.nid)
    mMessageListener.start()

    ## introduce a new application to the web server 
    app_api._send_handshake_msg(
        m_AppModel.nid, 
        m_AppModel.public_key,
        m_AppModel.created_at.isoformat(),
        api.MN_RKEY+str(0))
    



"""    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost", port=5672))
    channel = connection.channel()
    channel.queue_declare(queue=MSG_FROM_NODES)
    channel.basic_publish(exchange='',
                          routing_key=MSG_FROM_NODES,
                          body=json.dumps(
                            {
                            "action":_ACTION_KEYS[1],
                            "data":{
                                'nid':m_AppModel.nid, 
                                'public_key':m_AppModel.public_key, 
                                'created_at':m_AppModel.created_at.isoformat()
                                }
                            }))
    connection.close()"""






