import callme
import threading


class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        
    def run(self):
        server = callme.Server(server_id='haejong', amqp_host='localhost', amqp_port=5672)
        server.start()

mWebserver = WebServer()
mWebserver.start()