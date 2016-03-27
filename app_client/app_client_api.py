import threading
import sys
import json
import callme
sys.path.append(r'C:\Users\haejong\Desktop\Chatchat_distributed_system') 

from web_server.general_api import general_api as api
from client_model import AppModel, NodeModel

HOST_ADDR = "192.168.10.102"
logger = api.__get_logger('app_client.api.run')

class ActionControl:
    def __init__(self, private_key, uid):
        self.private_key = private_key
        self.uid = uid

    def register_client(self):
        def execute_command(encrypted_action):
            # decrypt msg
            data = json.loads(api.decrypt_msg(self.private_key, encrypted_action))
            action = data.pop('action',[])
            if (action == 'web_server_info'):
                _store_server_info(data)
            elif (action == 'remove_token'):
                remove_token()
            elif (action == 'receive_token'):
                receive_token(data['parameters']['token'])
            elif (data['action'] == 'add_text'):
                return add_text(data['parameters']['username'], data['parameters']['text'])
            elif (data['action'] == 'get_all_texts'):
                return get_all_texts()

        server = callme.Server(server_id=self.uid, amqp_host="localhost", threaded=True)
        server.register_function(execute_command, 'execute_command')
        server.start()


def _add_nodes(nodes):
    if nodes:
        models=[]
        for node in nodes:
            if node['uid'] != AppModel.objects.scalar('uid').get():
                models.append(NodeModel(uid=node.pop('uid',[]), public_key=node.pop('public_key',[])))
            else:
                print "it's yourself"

        if models:
            AppModel.objects.update(add_to_set__nodes=models)
            AppModel.objects.get().save()
            print AppModel.objects.to_json()   

    else:
        logger.error("nodes has no ele")


def _delete_node(uid):
    AppModel.objects.update(pull__nodes__uid=uid)
    AppModel.objects.get().save()
    print "deleted"
    print AppModel.objects.to_json()


def _store_server_info(server_data):
    data = server_data.pop('data',[])
    server_id = data.pop('server_id',[])
    server_public_key = data.pop('server_public_key',[])
    private_key_c = data.pop('private_key_c',[])

    if AppModel.objects.scalar('wsuid').get() is None:
        AppModel.objects.update_one(wsuid=server_id)
        AppModel.objects.update_one(server_public_key=server_public_key)
        AppModel.objects.update_one(private_key_c=private_key_c)
        print "server info stored"
        _send_heart_beat()
    else:
        logger.error("this client has no information of web server")
 

def _send_heart_beat():
    try:
        server_id = AppModel.objects.scalar('wsuid').get()
        proxy = callme.Proxy(server_id=server_id, amqp_host="localhost", timeout=2)
        proxy.use_server(server_id).receive_heart_beats(AppModel.objects.scalar('uid').get())
    except:
        pass
    threading.Timer(3, _send_heart_beat).start()

