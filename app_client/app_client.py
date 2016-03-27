import threading
import pika
import json
import sys
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

import app_client_api as app_api
import app_listener

from web_server.general_api import general_api as api
from mongoengine import *
from client_model import AppModel

HOST_ADDR = "192.168.10.102"
logger = api.__get_logger('app_client.run')

## [BEGIN] initiate a client with connection to db named 'chatchat'
connect('chatchat_c')

private_key = api.generate_private_key()
mAppModel = AppModel(public_key=api.generate_public_key(private_key).exportKey().decode('utf-8'), 
    uid=str(api.__uuid_generator_1()), private_key=private_key.exportKey().decode('utf-8'))
mAppModel.save()

app_id = mAppModel.uid
## [END]
#print mAppModel.public_key

logger.info("A new client instance created and it would notify the web server")
logger.info("client id: "+ mAppModel.uid)


if __name__ == "__main__":  

    ## pubsub - introduce a new application to the web server 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.queue_declare(queue='queue_where_new_client_joins')
    channel.basic_publish(exchange='',
                          routing_key='queue_where_new_client_joins',
                          body=json.dumps({'uid': mAppModel.uid, 
                            'public_key': mAppModel.public_key, 
                            'created_at':mAppModel.created_at.isoformat()}))

    ## register client functions
    mActionControl = app_api.ActionControl(mAppModel.private_key, mAppModel.uid)
    mActionControl.register_client()



