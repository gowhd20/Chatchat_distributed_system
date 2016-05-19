####################################
## Readable code versus less code ##
####################################

import threading
import pika
import json
import sys
import pickle
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

import app_client_api as app_api

from web_server.general_api import general_api as api
from web_server.general_api.connection_timeout import ConnTimeout
from client_model import AppModel
from app_core import Node
from server_listener import BroadcastListener, MessageListener
from mongoengine import *


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
    mNode = Node(pickle.dumps(m_AppModel))
    mNode.start()

    # listener for receiving broadcasted msg from the master server
    mBroadcastListener = BroadcastListener(m_AppModel.nid)
    mBroadcastListener.start()

    mMessageListener = MessageListener(m_AppModel.nid)
    mMessageListener.start()

    """timer = ConnTimeout(api._TIMEOUT,
            app_api._send_handshake_msg,
            servers=3, 
            args=[m_AppModel.nid, 
            m_AppModel.public_key, 
            m_AppModel.created_at.isoformat()])"""

    ## introduce a new application to the web server 
    app_api._send_handshake_msg(
        m_AppModel.nid, 
        m_AppModel.public_key,
        m_AppModel.created_at.isoformat(),
        api.MN_RKEY+str(0))
    





