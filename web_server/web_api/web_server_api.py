####################################
## Readable code versus less code ##
####################################

import callme
import threading
import pika
import json
import redis
import pickle
import bson

#from itsdangerous import Signer
from web_server.general_api import general_api as api
from web_server.general_api import redis_queue as q
from web_server.general_api.general_api import _ACTION_KEYS
from server_model import WebServerModel, ChildrenModel, ServerLogModel, Sessions
from shared_res_model import CommentListModel, CommentDetailModel, SharedSessions
from mongoengine import *

logger = api.__get_logger('web_server_api.run')


def _add_children(client, sid):
	s_obj = WebServerModel.objects(sid=sid)
	children = ChildrenModel(
		nid=client['nid'], 
    	created_at=client['created_at'], 
    	public_key=client['public_key'],
    	last_access=client['created_at'])
    	#last_work=api._get_current_time())
	s_obj.update_one(push__children=children)

	#s_obj.update_one(add_to_set__children=
    #    [ChildrenModel(nid=client['nid'], 
    #    	created_at=client['created_at'], 
    #    	public_key=client['public_key'],
    #    	last_access=client['created_at'])]).save()
	#s_obj.get().save()

	#print WebServerModel.objects.to_json()
	## make log of a new node joined
	_make_log(_ACTION_KEYS[1], sid, client['nid'])


## Deprecated	#################
def _create_usersession(uname, sid):
	sk = api._generate_session_key()

	mUserSession = UserSession(
			session_id=sk,
			username = uname
		)
	pk = WebServerModel.objects(sid=sid).get().public_key
	print pk
	return api.encrypt_msg(pk, sk)


def _find_usersession(secure_id, sid):
	pk = WebServerModel.objects(sid=sid).get().private_key
	s_id = api.decrypt_msg(pk, secure_id)

	return UserSession.objects(sid=sid).find_one({"session_id":s_id})
##################################


def _collect_session_garbages():
	garbage = []
	for s in Sessions.objects[:]:
		if s.expiration < api._get_current_time():
			garbage.append(s.ssid)

	if garbage:
		for s in garbage:
			Sessions.objects(ssid=s).delete()

	## temp
	#for s in Sessions.objects[:]:
	#	logger.info(s.expiration)


def _upload_user_sessions():
	ss_repl = map(lambda s:
				SharedSessions(
					created_at=s.created_at,
					by=s.by,
					ssid=s.ssid,
					user_data=s.user_data,
					expiration=s.expiration,
					modified=s.modified),
				Sessions.objects[:])
	try:
		res = SharedSessions.objects.insert(ss_repl)
	except(e):
		logger.error(e)
		return False
	else:
		## clean garbages in sessions
		_collect_session_garbages()
		return True


def _get_next_worker(sid):
	s_obj = WebServerModel.objects(sid=sid)
	lowest_time = api._get_current_time()

	for child in s_obj.get().children:
		if not 'last_work' in child:
			s_obj.filter(
				children__nid=child.nid).update_one(
				set__children__S__last_work=lowest_time) 	# set as now if new server
			s_obj.get().save()
			next_worker_id = child.nid


		elif child.last_work < lowest_time:
			lowest_time = child.last_work
			next_worker_id = child.nid

	print "next worker is... {}".format(next_worker_id)
	return next_worker_id

 
def _broadcast_to_nodes(queue_name, secure_data):
	if not isinstance(secure_data, str):
		secure_data = json.dumps(secure_data)

	try:
	    connection = pika.BlockingConnection(pika.ConnectionParameters(
	    	host="localhost", 
	    	port=5672))
	    channel = connection.channel()
	    channel.exchange_declare(exchange=queue_name,
	    	type='fanout')
	    channel.basic_publish(exchange=queue_name, 
	    	routing_key='', 
	    	body=secure_data)
	    connection.close()
	    return True

	except:
		logger.error("Broadcast failed")
		return False


def _coordinate_acc_to_res(sid, nid):
	if q.size() == 0:
		q.push(nid)
		WebServerModel.objects(sid=sid).update_one(last_access_to_res=nid)
		_make_log("resource_accessed", sid, nid)
		return True	

	else:
		q.push(nid)
		return False


def _refresh_common_key(sid):
	print "common key timeout"
	common_key_private = api.generate_private_key()
	s_obj = WebServerModel.objects(sid=sid)
	message = {
				"action":_ACTION_KEYS[3],
				"data":
				{
		    		"common_key_private":common_key_private.exportKey().decode('utf-8')
		    	}
			}

	try:
		if _broadcast_to_nodes(api.EXCHANGE_FOR_ALL, 
			api.encrypt_msg(s_obj.scalar('common_key_public').get(), 
			message)) == False:
			logger.error("Message broadcast failed")
			raise

		#else:
		res = s_obj.update_one(
			common_key_public=api.generate_public_key(common_key_private).exportKey().decode('utf-8'),
			common_key_private=message['data']['common_key_private'])
		s_obj.get().save()

		## make log of updated common key
		_make_log(_ACTION_KEYS[3], sid, "common key updated")

	except:
		logger.error("try again")
		raise

	threading.Timer(api.COMMON_KEY_TIMEOUT, _refresh_common_key, [sid]).start()


def _get_server_log(sid):
	return WebServerModel.objects(sid=sid).get().server_log
	#for log in logs:
	#	print log.to_json()


def _handshake_to_new_node(client, sid):
	## add client info into children document 
	_add_children(client, sid)
	s_obj = WebServerModel.objects(sid=sid)
	logger.info("client id:"+client['nid']+" has joined the system")

	message = json.dumps({
	    'action':_ACTION_KEYS[0], 
	    'data':
	        {
	            'server_id':s_obj.scalar('sid').get(), 
	            'server_public_key':s_obj.scalar('public_key').get(),
	            'common_key_private':s_obj.scalar('common_key_private').get()
	        }
	    })

	encrypted_message = api.encrypt_msg(client['public_key'], message)

	childs = s_obj.get().children
	message = {}

	for child in childs:
	    if not message:
	        message = {
	            'action':_ACTION_KEYS[1],
	            'data':[
	            {
	                'nid':child.nid,
	                'public_key':child.public_key
	            }]
	        }

	    else:
	        message['data'].append(
	            {
	                'nid':child.nid,
	                'public_key':child.public_key
	            })

	## TODO: set try and except
	retry = 0
	while retry < api.MAX_TRY:
		try:
			proxy = callme.Proxy(
				server_id=client['nid'], 
				amqp_host="localhost", 
				timeout=3)
			proxy.use_server(client['nid']).execute_command(encrypted_message)
			retry = api.MAX_TRY

		except:
			retry+=1
			print "passing master server info failed... {} times".format(retry)

		else:
			## broadcast of a new client to all nodes
			_broadcast_to_nodes(api.EXCHANGE_FOR_ALL, 
			    api.encrypt_msg(s_obj.scalar('common_key_public').get(),
			        json.dumps(message)))


def _inspect_inactive_children(sid):
	print "inspection...{}".format(sid)
	s_obj = WebServerModel.objects(sid=sid)

	children = s_obj.get().children
	#print children
	if children:
		for child in children:
			logger.info(child.last_access)
			logger.info(api._get_current_time())

			if api._get_unix_from_datetime(
				api._get_current_time())-api._get_unix_from_datetime(
				child.last_access)>api.TIME_DETERMINE_INACTIVE:

				logger.info(child.nid+" -> user logged out")
				## pull inactive user
				s_obj.update_one(pull__children__nid=child.nid)
				s_obj.get().save()

				## notify all clients about inactive user
				message = json.dumps(
					{
			        'action':_ACTION_KEYS[2],
			        'data':{
			            "nid":child.nid,
			            }
			        })

				_broadcast_to_nodes(api.EXCHANGE_FOR_ALL, 
					api.encrypt_msg(s_obj.scalar('common_key_public').get(),
						message))

				_make_log(_ACTION_KEYS[2], sid, child.nid)

				## TODO: try deamon thread
	threading.Timer(api.INSPECTION_TIME_INTERVAL, _inspect_inactive_children, [sid]).start()


def _check_node_accessing_to_res(nid, sid):
	if WebServerModel.objects(sid=sid).get().last_access_to_res == nid:
		return True
	else:
		return False


def _make_log(header, sid, log_txt):
	WebServerModel.objects(sid=sid).update_one(
		add_to_set__server_log=[
		ServerLogModel(
			by=sid, 
			header=header, 
			log=log_txt)
		])
	#WebServerModel.objects.get().save()


## routing message to specified routing_key, routing_key == node id
def _send_direct_msg(routing_key, msg):
	if not isinstance(msg, str):
	    msg = json.dumps(msg)

	connection = pika.BlockingConnection(pika.ConnectionParameters(
	    host="localhost", 
	    port=5672))
	channel = connection.channel()
	channel.exchange_declare(exchange=api.EXCHANGE_END_TO_END,
	                         type='direct')
	channel.basic_publish(exchange=api.EXCHANGE_END_TO_END,
	                      routing_key=routing_key,
	                      body=msg)
	connection.close()


def _update_last_access_time(nid, sid):
	collection = WebServerModel._get_collection()
	result = collection.update_one(
			{
				"_id":sid,
				"children._id":nid
			},
			{
				"$set":
				{
					"children.$.last_access":api._get_current_time()
				}
				
			})

	print result.modified_count
	print result.matched_count
	#print WebServerModel.objects.to_json()
	return True if result.modified_count == 1 and result.matched_count == 1 else False


## called by client when register
def receive_heartbeats(nid, sid):
	## if client registered
	if WebServerModel.objects(children__nid=nid):
		if _update_last_access_time(nid, sid) == False:
			logger.error(nid+" access_time update failed")
	else:
		logger.warning("user is not registered to the server")

"""
## checking queue status 
def queue_manager(nid, sid):
	if q.empty():
		return False

		elif
"""


"""collection = WebServerModel._get_collection()
result = collection.update_one(
	{
		"_id":mWebServerModel.nid
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
#WebServerModel.objects.update_one(set__children__last_access=general_api.get_current_time())
#print WebServerModel.objects.scalar('children.id').filter(nid=cid)
#WebServerModel.objects.update(push__server_log=ServerLogModel(log=log_txt))
#print WebServerModel.objects.filter(nid = 'vzWNmdPzlBpFyi6').scalar('server_log.log').to_json()

#    post = Post(uid='1', text="hi")
    #updated = Feed.objects(posts__uid=post.uid).update_one(set__posts__S=post)