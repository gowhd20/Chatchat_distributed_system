import callme
import threading

from web_server.general_api import general_api
from mongo_model import WebServerModel, ServerLogModel, ChildrenModel
from mongoengine import *

logger = general_api.get_logger('web_server_api.run')
WEB_SERVER_NAME = 'chatchat_web_server'

## [BEGIN] initiate the web server with connection to db named 'chatchat'
connect('chatchat')
WebServerModel.drop_collection()

## log
mServerLogModel = ServerLogModel(log="server initiated")

## create web server
KEY_LENGTH = 15
private_key = general_api.generate_private_key()
mWebServerModel = WebServerModel(public_key=general_api.generate_public_key(private_key).exportKey().decode('utf-8'), 
    uid=str(general_api.uuid_generator_4()), private_key=private_key.exportKey().decode('utf-8'))
mWebServerModel.server_log = [mServerLogModel]
mWebServerModel.save()
#print WebServerModel.objects.filter(uid = 'vzWNmdPzlBpFyi6').scalar('server_log.log').to_json()
## [END]

#def notify_clinet:


class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        
    def run(self):
        logger.info("the web server has been initiated")
        logger.info("web server id: "+mWebServerModel.uid)  
        ## register the server to the message broker
        server = callme.Server(server_id=WEB_SERVER_NAME, amqp_host='localhost', amqp_port=5672)
        server.start()

## run the web server 
mWebserver = WebServer()
mWebserver.start()