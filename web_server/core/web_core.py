####################################
## Readable code versus less code ##
####################################

from web_server.general_api import general_api as api
from web_server.web_api import web_server_api as server_api

import threading
import callme

logger = api.__get_logger('web_core.run')

class MasterServer(threading.Thread):
    def __init__(self, sid):
        self.sid = sid
        super(MasterServer, self).__init__()
        
    def run(self):

        ## start inspection on inactive clients
        server_api._inspect_inactive_children(self.sid)

        ## checking for timeout and refreshing common key
        threading.Timer(api.COMMON_KEY_TIMEOUT, 
            server_api._refresh_common_key, 
            [self.sid]).start()

        ## register the server to the message broker
        server = callme.Server(
            server_id=self.sid, 
            amqp_host="localhost",
            threaded=True, 
            amqp_port=5672)
        server.register_function(
            server_api.receive_heartbeats, 
            "receive_heartbeats")
        server.start()
