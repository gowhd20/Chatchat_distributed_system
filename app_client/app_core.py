####################################
## Readable code versus less code ##
####################################
import pickle
import dill
import threading
import pika
import json
import sys
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

import sys, time

#import app_listener
import callme
import app_client_api as app_api 

from web_server.general_api.connection_timeout import ConnTimeout
from web_server.general_api import general_api as api
from web_server.general_api.redis_queue import Queue

from client_model import AppModel

logger = api.__get_logger('app_client.run')
q = Queue(db=api.REDIS_ID_NODE)


class Node(threading.Thread):
    def __init__(self, model):
        self.model = pickle.loads(model)
        self.timer = ConnTimeout(api._TIMEOUT,
            app_api._send_handshake_msg,
            servers=3, 
            args=[self.model.nid, 
            self.model.public_key, 
            self.model.created_at.isoformat()])
        self.count = 0
        self.timer.start()
        super(Node, self).__init__()

        
    def run(self):
		logger.info("A new client instance created and it would notify the web server")
		logger.info("client id: "+ self.model.nid)

		server = callme.Server(
            server_id=self.model.nid, 
            amqp_host="localhost", 
            threaded=True, 
            amqp_port=5672)
		server.register_function(self.execute_command, 'execute_command')
		server.start()


    def execute_command(self, encrypted_action):
        print "server calling rpc"
        
        data = json.loads(
            api.decrypt_msg(self.model.private_key, encrypted_action))

        action = data['action']
        print action

        ## response from master server has arrived, stop trying to reach other servers
        if self.timer.is_alive():
            self.timer.stop()

        ## server sent info
        if (action == api._ACTION_KEYS[0]):
            self._store_server_info(data['data'], self.model.nid)

        ## add comments 
        elif(action == api._ACTION_KEYS[5]):
            data['nid'] = self.model.nid
            """data['content'].update(
                    {
                    'nid':self.model.nid,
                    'sid':data['sid']
                    })"""
        
            return api.encrypt_msg(AppModel.objects(
                nid=self.model.nid).get().server_public_key,
                    app_api.add_comments(**data))


    def _store_server_info(self, server_data, nid):
        try:
            AppModel.objects(nid=nid).update_one(
                master_sid=server_data['server_id'],
                server_public_key=server_data['server_public_key'],
                common_key_private=server_data['common_key_private'])

            print "server info updated"
            self._send_heartbeat(server_data['server_id'], nid)

        except:
            logger.error("this client has no information of master server")
     

    def _send_heartbeat(self, server_id, nid):
        retry = 0
        while retry < api.MAX_TRY:
            try:
                proxy = callme.Proxy(
                    server_id=server_id, 
                    amqp_host="localhost", 
                    amqp_port=5672, 
                    timeout=3)
                proxy.use_server(server_id).receive_heartbeats(nid, server_id)
                # try again
                retry = api.MAX_TRY

                ## record heartbeat locally as well
                AppModel.objects(nid=nid).update_one(last_access=api._get_current_time())
                is_master_failing = False
                    # try daemon thread
                #threading.Timer(3, _send_heart_beat).setDaemon(True)
                threading.Timer(api.CHECK_HEARTBEAT, self._send_heartbeat, [server_id, nid]).start()

            except:
                retry += 1
                is_master_failing = True
                print "Server: {} is not responding, trying {} times...".format(server_id, str(retry))

                #print "Master server is not responding"
                

        ## master server failed
        if is_master_failing:
            self.timer = ConnTimeout(api._TIMEOUT,
                        app_api._send_handshake_msg,
                        servers=3, 
                        args=[nid, 
                        AppModel.objects(nid=nid).get().public_key, 
                        AppModel.objects(nid=nid).get().created_at.isoformat()])
            self.timer.start()


            """_send_handshake_msg(
                nid, 
                AppModel.objects(nid=nid).get().public_key, 
                AppModel.objects(nid=nid).get().created_at.isoformat(), 
                api.MN_RKEY+str(1))"""
