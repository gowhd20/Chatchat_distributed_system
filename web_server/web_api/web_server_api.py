####################################
## Readable code versus less code ##
####################################

import callme
import threading
import pika
import json
import redis
import bson

#from itsdangerous import Signer
from web_server.general_api import general_api as api
from web_server.general_api.redis_queue import Queue

from server_model import WebServerModel, ChildrenModel, ServerLogModel, Sessions
from shared_res_model import CommentModel, UserSessions
from mongoengine import *

logger = api.__get_logger('web_server_api.run')

## for queueing turns for node to get the access to shared resource
q = Queue(db=api.REDIS_ID)

q.flush()


def _add_children(client, sid):
	s_obj = WebServerModel.objects(sid=sid)
	children = ChildrenModel(
		nid=client['nid'], 
    	created_at=client['created_at'], 
    	public_key=client['public_key'],
    	last_access=client['created_at'])
    	#last_work=api._get_current_time())
	s_obj.update_one(push__children=children)

	## make log of a new node joined
	_make_log(api._ACTION_KEYS[1], sid, client['nid'])


def _check_availability(sid):
	if WebServerModel.objects(sid=sid).get().children:
		return True
	else:
		return False


#	remove user sessions which has expired
def _clean_session_garbages():
	garbage = []
	for s in Sessions.objects[:]:
		if s.expiration < api._get_current_time():
			garbage.append(s.ssid)

	if garbage:
		for s in garbage:
			Sessions.objects(ssid=s).delete()


def _upload_user_sessions():
	try:
		for s in Sessions.objects[:]:
			if not UserSessions.objects(ssid=s.ssid):
				UserSessions(
					created_at=s.created_at,
					by=s.by,
					ssid=s.ssid,
					user_data=json.dumps(s.user_data),
					expiration=s.expiration,
					modified=s.modified).save()
			else:
				res = UserSessions.objects(ssid=s.ssid).update_one(
					by=s.by,
					user_data=json.dumps(s.user_data),
					expiration=s.expiration,
					modified=s.modified)
				#logger.info(res)

		logger.info(str(UserSessions.objects.count())+ "session ids are registered")
			

	except:
		logger.error("upload failed")
		return False
	else:
		## clean garbages in sessions
		_clean_session_garbages()
		return True


def _get_next_worker(sid):
	s_obj = WebServerModel.objects(sid=sid)
	lowest_time = api._get_current_time()

	for child in s_obj.get().children:
		## list of nodes failed once 
		if child.nid in q.get_custom_list(api.FAILED_NODES):
			print "failed nodes"
			print q.get_custom_list(api.FAILED_NODES)
			pass

		elif not 'last_work' in child:
			s_obj.filter(
				children__nid=child.nid).update_one(
				set__children__S__last_work=lowest_time) 	# set as now if new server
			s_obj.get().save()
			next_worker_id = child.nid


		elif child.last_work < lowest_time:
			lowest_time = child.last_work
			next_worker_id = child.nid
	
	try:
		s_obj.filter(
			children__nid=next_worker_id).update_one(
			set__children__S__last_work=api._get_current_time()) 
		s_obj.get().save()

		print "next worker is... {}".format(next_worker_id)
		return next_worker_id

	except NameError:
		logger.error("no workers are available")
		return None


def get_user_list(sid):
	if _coordinate_acc_to_res(sid=sid):
		if _upload_user_sessions():
			##	TODO: try with mongodb query but this requires to
			##	handle obtain 'modified' and convert into unix timestamp to compare
			##	within the query
			users = map(lambda x:{
					'user_name':json.loads(x.user_data)['user_name'],
					'modified':x['modified'],
					'ssid':x['ssid']
				} if api._get_unix_from_datetime(
					api._get_current_time())-api._get_unix_from_datetime(
					x.modified)<api.TIME_DETERMINE_USER_ACTIVE else None, 
					UserSessions.objects.all())

			#	release resource lock
			_coordinate_acc_to_res(sid, sid, 
						api._ACTION_KEYS[6])

			#	return list of lately active users by removing None values
			return filter(None, users)

		else:
			#	release resource lock
			_coordinate_acc_to_res(sid, sid, 
						api._ACTION_KEYS[6])
	else:
		users = map(lambda x:{
				'user_name':json.loads(x.user_data)['user_name'],
				'modified':x['modified'],
				'ssid':x['ssid']
			} if api._get_unix_from_datetime(
				api._get_current_time())-api._get_unix_from_datetime(
				x.modified)<api.TIME_DETERMINE_USER_ACTIVE else None, 
				Sessions.objects.all())

		return filter(None, users)

	return None


## send message to thirdparty nodes
def _broadcast_to_thirdparty(**data):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host="localhost", 
        port=5672))
    channel = connection.channel()
    channel.exchange_declare(exchange=api.TOPIC_NEW_NODE,
        type='topic')

    channel.basic_publish(exchange=api.TOPIC_NEW_NODE,
                            routing_key=api.TOPIC_MASTER_NODES,
                            body=json.dumps(
                            {
                            'action':api._ACTION_KEYS[7],
                            'data':{
                            	'sid':data['sid']
                            }}))
    connection.close()

 
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


def _coordinate_acc_to_res(sid=None, nid=None, action=None):
	## done working message from a node who has access to the shared resource
	if action == api._ACTION_KEYS[6]:
		q.pop()
		q.delete(api.RES_HOLDER)
		_make_log("resource_released", sid, nid)

		## next node in the queue
		nxt = q.bottom()
		if nxt:
			logger.info("next node exists")
			logger.info(nxt)

			#	if next resource accessor is master node himself
			if nxt == sid:
				_upload_user_sessions(sid)
				_coordinate_acc_to_res(sid, sid, 
							api._ACTION_KEYS[6])

			## save as node which holding lock to the resource at present
			q.append(api.RES_HOLDER, nxt)

			for child in WebServerModel.objects(sid=sid).get().children:
				if child.nid == nxt:
					_send_direct_msg(nxt, api.encrypt_msg(child.public_key, {
							'action':api._ACTION_KEYS[8],	# 	action : access permission
							'by':sid
						}))
					break

			_make_log("resource_lock", sid, nxt)
		else:
			logger.info("queue is empty")


		return True

	elif action == None and nid == None:
		if q.length() == 0:
			q.push(sid)
			#q.push(nid) 	# for debugging
			q.append(api.RES_HOLDER, sid)
			_make_log("resource_lock", sid, sid)
			return True	

		else:
			q.push(sid)
			return False

	elif action == None:
		for child in WebServerModel.objects(sid=sid).get().children:
			## node exists
			if child.nid == nid:
				if q.length() == 0:
					q.push(nid)
					#q.push(nid) 	# for debugging
					q.append(api.RES_HOLDER, nid)
					_make_log("resource_lock", sid, nid)
					return True	

				else:
					q.push(nid)
					return False

		## not registered node
		logger.error("not registered node")
		return False


def _clean_failed_garbages(sid):
	garbages = q.get_custom_list(api.FAILED_NODES)

	message = json.dumps(
		{
			'action':api._ACTION_KEYS[2],
			'data':garbages
			
		})

	_broadcast_to_nodes(
		api.EXCHANGE_FOR_ALL, 
		api.encrypt_msg(
			WebServerModel.objects(
			sid=sid).scalar(
			'common_key_public').get(),
			message))

	if WebServerModel.objects(sid=sid).update(pull_all__children=
		map(lambda x:{
				'nid':x
			}, garbages))>1:
		logger.info("cleaned failed nodes")
	else:
		logger.error("cleanning failed or nothing to clean")

	threading.Timer(api.CLEAN_GARBAGE_NODES, 
		_clean_failed_garbages, [sid]).start()		


def _refresh_common_key(sid):
	s_obj = WebServerModel.objects(sid=sid)

	if s_obj.get().children:
		logger.info("common key timeout")
		new_prk = api.generate_private_key()
		message = {
					"action":api._ACTION_KEYS[3],
					"data":
					{
			    		"common_key_private":new_prk.exportKey().decode('utf-8')
			    	}
				}

		try:
			if _broadcast_to_nodes(api.EXCHANGE_FOR_ALL, 
				api.encrypt_msg(s_obj.scalar('common_key_public').get(), 
				message)) == False:
				logger.error("Message broadcast failed")
				

			#else:
			res = s_obj.update_one(
				common_key_public=api.generate_public_key(new_prk).exportKey().decode('utf-8'),
				common_key_private=message['data']['common_key_private'])
			s_obj.get().save()

			## make log of updated common key
			_make_log(api._ACTION_KEYS[3], sid, "common key updated")

		except:
			logger.error("try again")
		
	
	threading.Timer(api.COMMON_KEY_TIMEOUT, _refresh_common_key, [sid]).start()


def _handshake_to_new_node(client, sid):
	## add client info into children document 
	_add_children(client, sid)
	s_obj = WebServerModel.objects(sid=sid)
	logger.info("client id:"+client['nid']+" has joined the system")

	message = json.dumps({
	    'action':api._ACTION_KEYS[0], 
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
	            'action':api._ACTION_KEYS[1],
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

#	Coarse-Gained Control
def _inspect_inactive_children(sid):
	#print "inspection...{}".format(sid)
	s_obj = WebServerModel.objects(sid=sid)

	children = s_obj.get().children

	if children:
		for child in children:
			#logger.info(child.last_access)
			#logger.info(api._get_current_time())

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
			        'action':api._ACTION_KEYS[2],
			        'data':{
			            "nid":child.nid,
			            }
			        })

				## remove lock on shared resource if the inactive child is holding it
				if q.get(api.RES_HOLDER) == child.nid:
					logger.info("logging out user had locks")
					_coordinate_acc_to_res(sid, child.nid, 
						api._ACTION_KEYS[6])

				_broadcast_to_nodes(api.EXCHANGE_FOR_ALL, 
					api.encrypt_msg(s_obj.scalar('common_key_public').get(),
						message))

				_make_log(api._ACTION_KEYS[2], sid, child.nid)

				## TODO: try deamon thread
	threading.Timer(api.INSPECTION_TIME_INTERVAL, _inspect_inactive_children, [sid]).start()


def _make_log(header, sid, log_txt):
	WebServerModel.objects(sid=sid).update_one(
		push__server_log=
		ServerLogModel(
			by=sid, 
			header=header, 
			log=log_txt)
		)

	logger.info("====================SERVER_LOG=====================")
	for log in WebServerModel.objects(sid=sid).get().server_log:
		logger.info(log.header +" : "+ log.log)
	logger.info("===================================================")


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


def _send_res_acc_call(nid):
	proxy = callme.Proxy(
		server_id=nid, 
		amqp_host="localhost", 
		timeout=3)


def _send_add_comment_call(**data):
	if data['nid'] == None:
		return False

	retry = 0
	prm = None

	while retry < api.MAX_TRY:
		try:
			# 	do not retry pushing node id inth the queue over as it failed first time
			if retry == 0:
				prm = _coordinate_acc_to_res(
									sid=data['sid'],
		    						nid=data['nid'])

			proxy = callme.Proxy(
				server_id=data['nid'], 
				amqp_host="localhost", 
				timeout=3)

			for c in WebServerModel.objects(sid=data['sid']).get().children:
			 	if c.nid == data['nid']:
					response = proxy.use_server(c.nid).execute_command(
						api.encrypt_msg(c.public_key, {
							'action':api._ACTION_KEYS[5],
							## access to shared resource has been permitted
							'permission':prm,
							'sid':data['sid'],
							'content':
							{
								'by':data['by'],
								'session_id':data['session_id'],
								'comment':data['comment'],
								'created_at':data['created_at']
							}
						}))
					return response
			## given node is not matching with any of registered node
			retry+=1
			print "trying {}".format(retry)
		except:
			retry+=1
			print "node {} is not responding.. trying {} times...".format(data['nid'], retry)

	# finally
	return False


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
	return True if result.modified_count == 1 and result.matched_count == 1 else False

#	Fine-Grained Control
def process_msg_add_request(sid, uname, ssid, comment):
    ## if master fails to find slave node, try MAX_TRY times until it
    ## response 503
    retry = 0
    while retry < api.MAX_TRY:
		try:
			node = _get_next_worker(sid)
			if node == None:
			    break
		    
			s_time = api._get_current_time().isoformat()
			response = _send_add_comment_call(**{
				'nid':node,
				'sid':sid,
				'by':uname,
				'session_id':ssid,
				'comment':comment,
				'created_at':s_time
			})

			if not response:
			    retry+=1
			    q.custom_push(api.FAILED_NODES, node)
			    logger.error("failed... trying another node...")

			## execution succeed
			else:
				return api.decrypt_msg(
					WebServerModel.objects(sid=sid).get().private_key, response)

		except:
			retry+=1
			logger.error("failed... trying another node...")

    return {
    	'errorMsg':"chatting is not available at the moment"
    }


## called by client when register
def receive_heartbeats(nid, sid):
	## if client registered
	if WebServerModel.objects(children__nid=nid):
		if _update_last_access_time(nid, sid) == False:
			logger.error(nid+" access_time update failed")
	else:
		logger.warning(nid+" is not registered to server")




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


def _get_server_log(sid):
	return WebServerModel.objects(sid=sid).get().server_log
	#for log in logs:
	#	print log.to_json()



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
