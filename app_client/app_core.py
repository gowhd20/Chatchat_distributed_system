####################################
## Readable code versus less code ##
####################################

import threading
import pika
import json
import sys
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

import app_client_api as app_api
#import app_listener
import callme

from web_server.general_api import general_api as api
from mongoengine import *
from client_model import AppModel


HOST_ADDR = "192.168.10.102"
logger = api.__get_logger('app_client.run')


class Node(threading.Thread):
    def __init__(self, nid, private_key):
    	self.nid = nid
    	self.private_key = private_key
        super(Node, self).__init__()

        
    def run(self):
		logger.info("A new client instance created and it would notify the web server")
		logger.info("client id: "+ self.nid)

		server = callme.Server(
            server_id=self.nid, 
            amqp_host="localhost", 
            threaded=True, 
            amqp_port=5672)
		server.register_function(self.execute_command, 'execute_command')
		server.start()


    def execute_command(self, encrypted_action):
        print "server calling rpc"
        data = json.loads(api.decrypt_msg(self.private_key, encrypted_action))
        action = data['action']
        print action

        ## server sent info
        if (action == api._ACTION_KEYS[0]):
            app_api._store_server_info(data['data'], self.nid)
        elif(action == api._ACTION_KEYS[5]):
            pass


        elif (action == 'ask_for_access'):
            remove_token()
        elif (action == 'receive_token'):
            receive_token(data['parameters']['token'])
        elif (data['action'] == 'add_text'):
            return add_text(data['parameters']['username'], data['parameters']['text'])
        elif (data['action'] == 'get_all_texts'):
            return get_all_texts()
