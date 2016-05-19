####################################
## Readable code versus less code ##
####################################

import threading
import sys
import json
import callme
import pika
import pickle
import dill
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system')  
        
from web_server.general_api import general_api as api
from web_server.general_api.connection_timeout import ConnTimeout
#from web_server.general_api.redis_queue import Queue    
from client_model import AppModel, NodeModel, CommentReplicaModel
from shared_res_model import CommentModel#CommentListModel

#q = Queue(db=api.REDIS_ID_NODE)

logger = api.__get_logger('app_client.api.run')
    
## RTC call
def add_comments(**data):   ## [{"by":"nid", "comment":"comment"}, ...]
    if not isinstance(data['content'], list):
        data['content'] = [data['content']]

    if data['permission']:

        for ele in data['content']:
            # TODO: compare also 'by' to make sure or set primary key for 'created_at'
            if not CommentModel.objects(timestamp=ele['created_at']):
                CommentModel(
                    by=ele['by'], 
                    timestamp=ele['created_at'], 
                    comment=ele['comment'],
                    session_id=ele['session_id'],
                    nid=data['nid']).save()

        response = []

        logger.info("=========================COMMENTS========================")
        for comment in CommentModel.objects.all():
            logger.info(str(comment.timestamp)+" : "+comment.by+" : "+comment.comment)

            #   prepare return data, return all the comment values from shared resource
            response.append({
                    'by':comment.by,
                    'timestamp':comment.timestamp.isoformat(),
                    'comment':comment.comment
                })

            #   if data is not already stored locally
            if not CommentReplicaModel.objects(timestamp=comment.timestamp.isoformat()):
                #   replicate
                CommentReplicaModel(
                    by=comment.by, 
                    timestamp=comment.timestamp.isoformat(), 
                    comment=comment.comment,
                    session_id=comment.session_id,
                    nid=comment.nid).save()

        logger.info("=========================================================")

        ## send response 'release' action to the master server
        _send_direct_msg(data['sid'], {
                'action':api._ACTION_KEYS[6],
                'data':{
                    'nid':data['nid']
                }
            })

        return response


    ## no permission to access to the shared resource
    else:
        logger.info("no access")
        logger.info(data['content'])

        for ele in data['content']:
            CommentReplicaModel(
                by=ele['by'], 
                timestamp=ele['created_at'], 
                comment=ele['comment'],
                session_id=ele['session_id'],
                nid=data['nid']).save()

        response = []

        ## display/return only locally stored data
        logger.info("=========================COMMENTS========================")
        for comment in CommentReplicaModel.objects.all():
            logger.info(str(comment.timestamp)+" : "+comment.by+" : "+comment.comment)
            response.append({
                    'by':comment.by,
                    'timestamp':comment.timestamp.isoformat(),
                    'comment':comment.comment
                })
        logger.info("=========================================================")
        return response


## nodes : list of other server nodes,
## nid : myself
def _add_nodes(nodes, nid):
    if nodes:
        active_nodes=[]
        for node in nodes:
            if api.uuid_to_obj(node['nid'] is None or api.uuid_to_obj(nid) is None):
                logger.error("wrong type of user id")

            elif node['nid'] != nid:
                active_nodes.append(NodeModel(
                    nid=node['nid'], 
                    public_key=node['public_key']))

            else:
                #print "it's yourself"
                pass

        if active_nodes:
            n_obj = AppModel.objects(nid=nid) 
            n_obj.update(add_to_set__nodes=active_nodes)
            n_obj.get().save()

            logger.info("new node joined, current active node list") 
            nodes = n_obj.get().nodes

            for node in nodes:
                node_obj = json.loads(node.to_json())
                print "id: {}".format(node_obj['_id'])

    else:
        logger.error("nodes has no element")


## very first message to the master node
def _send_handshake_msg(nid, public_key, created_at, r_key):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host="localhost", 
        port=5672))
    channel = connection.channel()
    channel.exchange_declare(exchange=api.TOPIC_NEW_NODE,
        type='topic')

    channel.basic_publish(exchange=api.TOPIC_NEW_NODE,
                            routing_key=r_key,
                            body=json.dumps(
                            {
                            "action":api._ACTION_KEYS[1],
                            "data":{
                                'nid':nid, 
                                'public_key':public_key, 
                                'created_at':created_at
                                }
                            }))
    connection.close()


## routing message to specified routing_key
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


def _delete_nodes(target_nids, my_nid):
    n_obj = AppModel.objects(nid=my_nid)

    if not isinstance(target_nids, list):
        if n_obj.update_one(pull__nodes__nid=target_nids)>0:
            n_obj.get().save()
            logger.info(target_nids+" deleted")
        else:
            logger.error("deleted failed")

    else:
        if n_obj.update(pull_all__nodes=
            map(lambda x:{
                'nid':str(x)
            }, target_nids))>0:
            n_obj.get().save()

            logger.info("deleted many")
        else:
            logger.error("deleted many failed")

    nodes = n_obj.get().nodes
    for node in nodes:
        node_obj = json.loads(node.to_json())
        print "id: {}".format(node_obj['_id'])


def _refresh_common_key(nid, key):
    if AppModel.objects(nid=nid).update_one(common_key_private=key)>0:
        return True
    else:
        return False

