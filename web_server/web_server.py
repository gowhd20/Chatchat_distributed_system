# coding=utf-8

import logging
import threading

from web_api import web_server_api, new_client_listener

from flask_restful import Resource
from flask import render_template, Blueprint, Response, request, session, g

from source.api.event_stream import event_stream

global users


users = {};

web_server = Blueprint('web_server', __name__,
                     static_folder='static',
                     template_folder='templates')

global init

@web_server.before_request
def before_request():
    g.user = None
    #print g
    #print request.cookies
    print request.cookies

@web_server.route('/', methods=['POST', 'GET'])
def index():
    global init
    logging.warning('yes sir')
    page = 'overview'
    data = {
        'page': page,
    }
    if request.method == 'POST' and 'user_name' in request.form.keys() and request.form['user_name'].strip() != '':
        session['user_name'] = request.form['user_name'].strip()
        user_name = request.form['user_name'].strip()
        data = {'user_name' : user_name}
        #print data
        if user_name not in users:
            users[user_name] = {'user_name':user_name, 'session_id':general_api.random_id_generator()}
            #print users
		
        return render_template('msg.html', response_data=data)

    return render_template('index.html', **data)


@web_server.route('/send_msg', methods=['POST'])
def send_msg():
    global users
	# check if the user is logged in, if not send redirect signal
    if 'user' not in g or g.user is None:
        return '{"action" : "REDIRECT", "data":{"href":"/"}}'
    user_name = session['user_name']
    print session['user_name']
    if user_name not in users:
        users[user_name] = {'user_name': user_name, 'session_id': general_api.random_id_generator()}

    returned_data = '';
    if request.form.get('msg_txt') is not None and str(request.form.get('msg_txt')).strip() != '':
        text = str(request.form.get('msg_txt')).strip()
        print text
        #next_worker = get_next_worker()
        #next_worker_proxy = callme.Proxy(server_id=next_worker['id'], amqp_host=hostname)
        #data
		#returned_data = next_worker_proxy.use_server(next_worker['id']).add_text(username, chat_text)
        #log_data(next_worker['id'], 'user "' +username + '" send text')
        #returned_data = json.dumps({"signal" : 'ADDED_TO_SERVER'})
        return_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}'
    else:
        return_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}' 

    return return_data
	