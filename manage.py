from gevent.monkey import patch_all
patch_all()

from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.script import Manager, Server

from web_server.web_server import web_server
from web_server.views.user import user_blueprint

from mongo_engine import app

HOST_ADDR = "192.168.10.102"
app.register_blueprint(web_server,  url_prefix='/web_server')
app.register_blueprint(user_blueprint, url_prefix='/web_server/user')

from gevent.wsgi import WSGIServer
try:
    http_server = WSGIServer((HOST_ADDR, 1327), app)
    http_server.serve_forever()
except KeyboardInterrupt:
    print 'Exiting'
