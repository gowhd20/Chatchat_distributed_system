####################################
## Readable code versus less code ##
####################################

import threading
import sys
import json
import callme
import pika
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system')  

from web_server.general_api import general_api as api
from web_server.general_api import redis_queue as q
from client_model import AppModel, NodeModel
from shared_res_model import CommentListModel


MSG_FROM_NODES = "msg_from_nodes"
HOST_ADDR = "192.168.10.102"
logger = api.__get_logger('app_client.api.run')
CHECK_HEARTBEAT = 5
is_master_failing = False


## RTC call
def add_comment_request(data):
    if data['permission']:
        collection = CommentListModel._get_collection()
        res = collection.update(
            {},
            {
                "$push":
                {
                    "comments":
                    {
                        "$each":data    ## [{"by":"nid", "comment":"comment"}, ...]
                    }
                }
            },
            upsert=True)

        for i in CommentListModel.objects:
            for j in i.comments:
                print j.to_json()

        return {
            "message":"inserted"
            } if res['n']>0 and res['nModified']>0 or res['upserted'] else {
                "message":"error"
                }
    else:
        q.push(data['details'])
        return {
            "message":"cached"
        }



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
        type='topic',durable=True)

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
    channel.exchange_declare(exchange='direct_msg',
                             type='direct')
    channel.basic_publish(exchange='direct_msg',
                          routing_key=routing_key,
                          body=msg)
    connection.close()


def _delete_node(target_nid, my_nid):
    n_obj = AppModel.objects(nid=my_nid)
    n_obj.update_one(pull__nodes__nid=target_nid)
    n_obj.get().save()
    print "deleted"

    nodes = n_obj.get().nodes
    for node in nodes:
        node_obj = json.loads(node.to_json())
        print "id: {}".format(node_obj['_id'])
    #print AppModel.objects.to_json()


def _store_server_info(server_data, nid):
    #if AppModel.objects(nid=nid).scalar('master_sid').get() is None:
    try:
        AppModel.objects(nid=nid).update_one(
            master_sid=server_data['server_id'],
            server_public_key=server_data['server_public_key'],
            common_key_private=server_data['common_key_private'])

        print "server info updated"
        _send_heartbeat(server_data['server_id'], nid)

    except:
        logger.error("this client has no information of master server")
 

def _send_heartbeat(server_id, nid):
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
            threading.Timer(3.0, _send_heartbeat, [server_id, nid]).start()
        except:
            retry += 1
            is_master_failing = True
            print "Master server is not responding"
            

    ## default server failed
    if is_master_failing:
        #for ms in api.IDS:
        #    try:

        _send_handshake_msg(
            nid, 
            AppModel.objects(nid=nid).get().public_key, 
            AppModel.objects(nid=nid).get().created_at.isoformat(), 
            api.MN_RKEY+str(1))



def _refresh_common_key(nid, key):
    if AppModel.objects(nid=nid).update_one(common_key_private=key)>0:
        return True
    else:
        return False



