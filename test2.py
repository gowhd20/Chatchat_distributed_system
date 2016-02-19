from gevent.wsgi import WSGIServer
import redis
import threading
from flask import Flask

app = Flask(__name__)
#http_server = WSGIServer(('', 5555), app)
#http_server.serve_forever()

red = redis.StrictRedis()


channel = "exclusive"
	
pubsub = red.pubsub()
pubsub.subscribe(channel)


class ServerListener (threading.Thread):
    def __init__(self):
        super(ServerListener, self).__init__()
    def run(self):
        listener(self)
        
def listener(self):
    print "i am listening"
    server_listeneing_loop()   		

def server_listeneing_loop():
    print "listening to channel exclusive"
    for message in pubsub.listen():
        print message['data']
    threading.Timer(1, server_listeneing_loop).start()

mServerListener = ServerListener()
mServerListener.run()