import pika
import threading
import json

def printo(a, b, c, d):
    print a
    print b
    print c
    d = json.loads(d)
    print d.public_key
    print 'new server added'

class NewServerListener(threading.Thread):
    def __init__(self):
        super(NewServerListener, self).__init__()
        
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        
        channel.queue_declare(queue='awaiting_new_app_server')
        
        channel.basic_consume(printo,
                              queue='awaiting_new_app_server',
                              no_ack=True)
        
        #print(datetime.datetime.now(), '  [*] Waiting for servers')
        channel.start_consuming()


mServerListener = NewServerListener()
mServerListener.start()