####################################
## Readable code versus less code ##
####################################

# coding=utf-8

import logging
import threading
import json

from core.web_core import MasterServer
from general_api import general_api as api
from flask_restful import Resource
from flask import render_template, Blueprint, Response, request, session, g, make_response
from mongo_engine import app

from source.api.event_stream import event_stream

from web_api import web_server_api as server_api

#from mongo_session import MongoSessionInterface

from server_model import WebServerModel, ServerLogModel, Sessions, MongoSessionInterface
from shared_res_model import CommentListModel, CommentDetailModel,SharedSessions   ## temp for db drop
from client_model import AppModel       ## temp for db drop
from mongoengine import *

from .web_api.node_listener import NewNodeListener, NodeMessageListener

logger = api.__get_logger('web_server.run')

## [BEGIN] initiate the web server with connection to db named 'chatchat'
connect('chatchat')
#WebServerModel.drop_collection()
#AppModel.drop_collection()  ## temp
#CommentListModel.drop_collection()  ## temp
#Sessions.drop_collection()  ## temp
#SharedSessions.drop_collection() ## temp


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

@web_server.before_request
def before_request():
    g.user = None
    #print g
    #print request.cookies
    #print "hey yoooooo"
    #print request.cookies.get('tasty_cookie')


@web_server.after_request
def call_after_request_callbacks(response):
    #print response
    #response.set_cookie("tasty_cookie", value="nacho")
    #return response 
    return response

@web_server.route('/', methods=['POST', 'GET'])
def index():
    print session
 
    page = 'overview'
    resp = {
        'page': page
    }

    if request.method == 'POST' and 'user_name' in request.form.keys():

        if request.form['user_name'] == '':
            resp['errorMsg'] = "user name should not be an empty string"
            return app.make_response(render_template('index.html', **resp))

        else:
            uname = request.form['user_name']
            ## user id is not registered to the db
            if(not 'user_name'in session):
                session['user_name'] = uname

            resp = {
                "user_name":uname,
                }

        return app.make_response(render_template('msg.html', response=resp))

#    elif request.cookies.get('sid'):
#        print "found cookie!!"

    return app.make_response(render_template('index.html'))


@web_server.route('/send_msg', methods=['POST'])
def send_msg():
    global users
	# check if the user is logged in, if not send redirect signal
    if 'user' not in g or g.user is None:
        return '{"action" : "REDIRECT", "data":{"href":"/"}}'
    user_name = session['user_name']
    print session['user_name']
    if user_name not in users:
        users[user_name] = {'user_name': user_name, 'session_id': api.random_id_generator()}

    returned_data = '';
    if request.form.get('msg_txt') is not None and str(request.form.get('msg_txt')).strip() != '':
        text = str(request.form.get('msg_txt')).strip()
        print text

        return_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}'
    else:
        return_data = '{"action" : "ERROR", "data":{"error_message" : "Text cannot be blank!!!"}}' 

    return return_data


