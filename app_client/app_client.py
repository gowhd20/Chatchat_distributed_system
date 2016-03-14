import threading
import pika
import json


class AppClient(threading.Thread):
    def __init__(self):
        super(AppClient, self).__init__()
        
    def run(self):
        global token, queueing_texts, app_server, gateway_id

if __name__ == "__main__":
    #print(datetime.datetime.now(), ' Start server ', app_server.id)
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='awaiting_new_app_server')
    channel.basic_publish(exchange='',
                          routing_key='awaiting_new_app_server',
                          body=json.dumps({'id': 'app_client_id', 'public_key': 'public_key'}))
    connection.close()

app_client = AppClient()
app_client.start()