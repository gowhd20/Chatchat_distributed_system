# coding=utf-8

import logging
import redis
import threading

from flask_restful import Resource, Api

from flask import render_template, Blueprint, Response, request

from source.api.event_stream import event_stream

config = {
	'host' : 'localhost',
	'port' : 5555,
	'db'   : 0,
}

red = redis.StrictRedis()

client = Blueprint('client', __name__,
                     static_folder='static',
                     template_folder='templates')



@client.route('/', methods=['POST', 'GET'])
def index():
    logging.warning('yes sir')
    page = 'overview'
    data = {
        'page': page,
    }
    if request.method == 'POST' and 'username' in request.form.keys() and request.form['username'].strip() != '':
        data = request.form['username'].strip()
        print data
        data = {'username' : data}
        return render_template('chat.html', data=data)

    return render_template('index.html', **data)
	
channel = "exclusive"
	
pubsub = red.pubsub()
pubsub.subscribe(channel)
	
@client.route('/send_chat', methods=['POST'])
def send_chat():
    returned_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}'
    chat_text = str(request.form.get('chat_text')).strip()
    print chat_text
    red.publish(channel, returned_data)
    return returned_data


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


@client.route('/event_listener/<tagID>')
def stream(tagID):
    print "Connection started"
    resp = Response(event_stream(tagID), mimetype="text/event-stream")
    return resp
	
	


