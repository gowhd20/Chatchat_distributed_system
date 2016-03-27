from server_model import WebServerModel
from client_model import AppModel		## temp for db drop
from mongoengine import *
from web_server.general_api import general_api as api
from web_server.web_api import web_server_api as web_api

import threading
import callme

## [BEGIN] initiate the web server with connection to db named 'chatchat'
connect('chatchat')
WebServerModel.drop_collection()
AppModel.drop_collection()	## temp

logger = api.__get_logger('web_core.run')

## create web server
private_key = api.generate_private_key()
private_key_c = api.generate_private_key()
mWebServerModel = WebServerModel(public_key=api.generate_public_key(private_key).exportKey().decode('utf-8'),
	public_key_c=api.generate_public_key(private_key_c).exportKey().decode('utf-8'),
    uid=str(api.__uuid_generator_4()), 
    private_key=private_key.exportKey().decode('utf-8'),
    private_key_c=private_key_c.exportKey().decode('utf-8'))
mWebServerModel.save()
## log
web_api._logging_action("server initiated")
## [END]

class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        
    def run(self):

        logger.info("the web server has been initiated")
        logger.info("web server id: "+mWebServerModel.uid)

        ## start inspection on inactive clients
        web_api._inspect_inactive_children()

        ## register the server to the message broker
        server = callme.Server(server_id=mWebServerModel.uid, amqp_host="localhost", amqp_port=5672)
        server.register_function(web_api.receive_heart_beats, "receive_heart_beats")
        server.start()

## run the web server 
mWebserver = WebServer()
mWebserver.start()