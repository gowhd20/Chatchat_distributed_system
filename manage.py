from gevent.monkey import patch_all
patch_all()

from logging import getLogger
from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.script import Manager, Server

from client.blueprint import client
from client.views.user import user_blueprint
from mongoengine import *

connect('chatchat')

logger = getLogger('watson.run')

from mongo_engine import app

app.register_blueprint(client,  url_prefix='/client')
app.register_blueprint(user_blueprint, url_prefix='/client/user')


app.debug = True


from gevent.wsgi import WSGIServer

http_server = WSGIServer(('', 5555), app)
http_server.serve_forever()
