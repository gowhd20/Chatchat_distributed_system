import callme
import threading
import pika
import json

from web_server.general_api import general_api as api
from server_model import WebServerModel, ChildrenModel, ServerLogModel
from mongoengine import *

logger = api.__get_logger('web_server_api.run')
TIME_DETERMINE_INACTIVE = 10		## 5 sec => test purpose 
BROADCAST_QUEUE = "queue_where_it_listen_to_broadcast"
HOST_ADDR = "192.168.10.102"

def _add_children(uid, create_at, public_key):
	WebServerModel.objects.update(add_to_set__children=
        [ChildrenModel(uid=uid, created_at=create_at, public_key=public_key)])
	WebServerModel.objects.get().save()
	## add log
	_logging_action("A children added")


def _broadcast_to_nodes(queue_name, secure_data):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost", port=5672))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange='', 
    	routing_key=queue_name, 
    	body=secure_data)


def _get_server_log_instance():
	return WebServerModel.objects.get().server_log
	#for log in logs:
	#	print log.to_json()


def _inspect_inactive_children():
	print "inspection..."
	children = WebServerModel.objects.get().children
	#print children
	if children:
		for child in children:
			if api.__get_unix_from_datetime(api.__get_current_time())-api.__get_unix_from_datetime(child.timestamp_last_access)>TIME_DETERMINE_INACTIVE:
				logger.info(child.uid+" -> user logged out")
				## pull inactive user
				WebServerModel.objects.update(pull__children__uid=child.uid)
				WebServerModel.objects.get().save()
				## notify all clients about inactive user
				message = json.dumps({
			        'action':'remove_inactive_client',
			        'data':{
			            "uid":child.uid,
			            }
			        })
				_broadcast_to_nodes(BROADCAST_QUEUE, 
					api.encrypt_msg(WebServerModel.objects.scalar('public_key_c').get(),
						message))
	threading.Timer(3, _inspect_inactive_children).start()


def _logging_action(log_txt):
	WebServerModel.objects.update(add_to_set__server_log=[ServerLogModel(log=log_txt)])
	WebServerModel.objects.get().save()


def _update_last_access_time(uid):
	collection = WebServerModel._get_collection()
	result = collection.update_one(
			{
				"_id":WebServerModel.objects.scalar('uid').get(),
				"children._id":uid
			},
			{
				"$set":
				{
					"children.$.timestamp_last_access":api.__get_current_time()
				}
				
			})
	print result.modified_count
	print result.matched_count
	return True if result.modified_count == 1 and result.matched_count == 1 else False


## called by client when register
def receive_heart_beats(uid):
	## if client registered
	if WebServerModel.objects(children__uid=uid):
		if _update_last_access_time(uid) == False:
			logger.error(uid+" access_time update failed")
	else:
		logger.warning("user is not registered to the server")



"""collection = WebServerModel._get_collection()
result = collection.update_one(
	{
		"_id":mWebServerModel.uid
	},
	{
		"$set":{
			"public_key":"random"
		}
	})
print result.modified_count
print result.matched_count 
print WebServerModel.objects.scalar('public_key').get()"""

"""
	logs = WebServerModel.objects.get().server_log
	for log in logs:
		print log.to_json()"""

#WebServerModel.objects.get().server_log.append(ServerLogModel(log=log_txt))
#WebServerModel.objects.update_one(set__children__timestamp_last_access=general_api.get_current_time())
#print WebServerModel.objects.scalar('children.id').filter(uid=cid)
#WebServerModel.objects.update(push__server_log=ServerLogModel(log=log_txt))
#print WebServerModel.objects.filter(uid = 'vzWNmdPzlBpFyi6').scalar('server_log.log').to_json()

