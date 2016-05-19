####################################
## Readable code versus less code ##
####################################

# coding=utf-8

import logging
import threading
import json
import callme

from core.web_core import MasterServer
from general_api import general_api as api
from flask import render_template, Blueprint, request, session, g, make_response, redirect, url_for
from mongo_engine import app
from flask.ext.cors import CORS

from source.api.event_stream import event_stream

from web_api import web_server_api as server_api

#from mongo_session import MongoSessionInterface

from server_model import WebServerModel, Sessions, MongoSessionInterface
from shared_res_model import CommentModel, UserSessions   ## temp for db drop
from client_model import AppModel, CommentReplicaModel       ## temp for db drop
from mongoengine import *

from .web_api.node_listener import NewNodeListener, NodeMessageListener

logger = api.__get_logger('web_server.run')

## [BEGIN] initiate the web server with connection to db named 'chatchat'
connect('chatchat')
#WebServerModel.drop_collection()   #tmemp
#AppModel.drop_collection()  ## temp
#CommentModel.drop_collection()  ## temp
#Sessions.drop_collection()  ## temp
#UserSessions.drop_collection() ## temp
#CommentReplicaModel.drop_collection() ## temp

## allow cross-origin requests
CORS(app)

## create web server
private_key = api.generate_private_key()
common_key_private = api.generate_private_key()

mWebServerModel = WebServerModel(
    public_key=api.generate_public_key(private_key).exportKey().decode('utf-8'),
    sid=str(api.__uuid_generator_4()),
    #session_key='secret',   # temp use instead  api._get_session_key(), 
    private_key=private_key.exportKey().decode('utf-8'),
    common_key_private=common_key_private.exportKey().decode('utf-8'),
    common_key_public=api.generate_public_key(common_key_private).exportKey().decode('utf-8'))
mWebServerModel.save()

logger.info("Master server has been initiated")
logger.info("Server id: "+mWebServerModel.sid)

##  this class manages users' session in the db
app.session_interface = MongoSessionInterface(
    db='chatchat', by=mWebServerModel.sid)

## log
server_api._make_log("server_init", mWebServerModel.sid, "server initiated")
## [END]
    
## run the master server 
mMasterServer = MasterServer(mWebServerModel.sid)
mMasterServer.start()

## receiving direct message
mNodeMessageListener = NodeMessageListener(mWebServerModel.sid)
mNodeMessageListener.start()

## receiving through queue name
mNewNodeListener = NewNodeListener(mWebServerModel.sid)
mNewNodeListener.start()

web_server = Blueprint('web_server', __name__,
                     static_folder='static',
                     template_folder='templates')

#server_api._upload_user_sessions()

@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


@web_server.before_request
def before_request():
    g.user = None

    #print request.cookies.get('tasty_cookie')


@web_server.after_request
def call_after_request_callbacks(response):
 
    return response


@web_server.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST' and 'user_name' in request.form.keys():
        if request.form['user_name'] == '':
            resp['errorMsg'] = "user name should not be an empty string"
            return app.make_response(render_template('index.html', **resp))

        else:
            uname = request.form['user_name']
            ## user id is not registered to the db
            #if(not 'user_name' in session):
            session['user_name'] = uname

        resp = {'user_name':uname}
        users = server_api.get_user_list(mWebServerModel.sid)

        if users:
            resp['active_users'] = users

        return app.make_response(render_template('msg.html', 
            response=resp))

    elif request.method == 'GET' and 'user_name' in session:
        resp = {'user_name':session['user_name']}
        users = server_api.get_user_list(mWebServerModel.sid)

        if users:
            resp['active_users'] = users

        return app.make_response(render_template('msg.html', 
            response=resp))

    return app.make_response(render_template('index.html'))


@web_server.route('/send_msg', methods=['POST'])
def send_msg():
	## user has not provided name for chat
    text = request.form.get('content')

    if not 'user_name' in session:
        return redirect(url_for('web_server.index'), 401)

    res = server_api.process_msg_add_request(
        mWebServerModel.sid,
        session['user_name'],
        request.cookies.get(app.session_cookie_name),
        text)

    if 'errorMsg' in res:
        url = 'http://'+api.HOST_ADDR+':'+str(api.PORT+1)+'/web_server'
        return redirect(url, 503)
        #return json.dumps(res), 503

    else:
        ## return all history of comments
        return json.dumps({
                'response':"STORED",
                'contents':res
            }), 201


@web_server.route('/get_comments', methods=['GET'])
def get_comments():
    pass


@web_server.route('/check_availability', methods=['GET'])
def check_availability():
    return str(server_api._check_availability(mWebServerModel.sid)), 200


"""
returned_data = '';
if request.form.get('msg_txt') is not None and str(request.form.get('msg_txt')).strip() != '':
    text = str(request.form.get('msg_txt')).strip()
    print text

    return_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}'
else:
    return_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}' 
"""


