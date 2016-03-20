import threading
import sys
import json
import callme
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 
from web_server.general_api import general_api
#from app_client import mAppModel

logger = general_api.get_logger('app_client.api.run')
#global private_key, uid




class ActionControl:
    def __init__(self, private_key, uid):
        self.private_key = private_key
        self.uid = uid

    def registerServer(self):
        def execute_command(encrypted_action):
            #print self.private_key
            #print encrypted_action
            global private_key
            #print private_key
            data = json.loads(general_api.decrypt_msg(self.private_key, encrypted_action))
            if (data['action'] == 'recognize_gateway'):
                print "done"
                #recognize_gateway(data['parameters']['gateway_id'], data['parameters']['gateway_public_key'])
            elif (data['action'] == 'remove_token'):
                remove_token()
            elif (data['action'] == 'receive_token'):
                receive_token(data['parameters']['token'])
            elif (data['action'] == 'add_text'):
                return add_text(data['parameters']['username'], data['parameters']['text'])
            elif (data['action'] == 'get_all_texts'):
                return get_all_texts()

        server = callme.Server(server_id=self.uid, amqp_host='localhost', threaded=True)
        server.register_function(execute_command, 'execute_command')
        server.start()