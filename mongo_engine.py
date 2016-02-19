from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.script import Manager, Server

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "chatchat"}
app.config["SECRET_KEY"] = "s2haejong"


config = {
	'host' : 'localhost',
	'port' : 6379,
	'db'   : 0,
}

channel = "exclusive"

db = MongoEngine(app)
