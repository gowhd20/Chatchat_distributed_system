import callme
import threading

def add(a, b):
    return a + b

class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        
    def run(self):
        server = callme.Server(server_id='haejong', amqp_host='localhost', amqp_port=5672)
        print 'adding add'
        server.register_function(add, 'add')
        server.start()

mWebserver = WebServer()
mWebserver.start()
print 'do you come herer?'
	