# coding=utf-8

import logging
import threading

from flask_restful import Resource

from flask import render_template, Blueprint, Response, request

from source.api.event_stream import event_stream
from mongo_engine import config, channel


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
        #OpenChatChannel()
        return render_template('chat.html', data=data)

    return render_template('index.html', **data)


@client.route('/', methods=['POST'])
def OpenChatChannel():
    print "Connection started"
    resp = Response(event_stream('haejong'), mimetype="text/event_chat")
    return resp
	

	

