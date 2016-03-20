import threading
import pika
import json
import sys
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

import app_client_api as app_api
from web_server.general_api import general_api
from mongoengine import *
from mongo_model import AppModel

logger = general_api.get_logger('app_client.run')

## [BEGIN] initiate a client with connection to db named 'chatchat'
connect('chatchat')
AppModel.drop_collection()
KEY_LENGTH = 15
private_key = general_api.generate_private_key()
mAppModel = AppModel(public_key=general_api.generate_public_key(private_key).exportKey().decode('utf-8'), 
    uid=str(general_api.uuid_generator_1()), private_key=private_key.exportKey().decode('utf-8'))
mAppModel.save()
## [END]
#print mAppModel.public_key

logger.info("A new client instance created and it would notify the web server")
logger.info("client id: "+ mAppModel.uid)


if __name__ == "__main__":  

    ## pubsub - introduce a new application to the web server 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='queue_where_new_client_joins')
    channel.basic_publish(exchange='',
                          routing_key='queue_where_new_client_joins',
                          body=json.dumps({'uid': mAppModel.uid, 
                            'public_key': mAppModel.public_key, 
                            'created_at':mAppModel.created_at.isoformat()}))
    mActionControl = app_api.ActionControl(mAppModel.private_key, mAppModel.uid)
    mActionControl.registerServer()



