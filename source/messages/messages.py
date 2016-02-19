from flask import Flask
import redis
from flask_restful import Resource, Api
from mongoengine import *
from source.api.event_stream import event_stream

try:
    from flask_cors import cross_origin
    # support local usage without installed package
except:
    from flask.ext.cors import cross_origin
    # this is how you would normally import

app = Flask(__name__)
api = Api(app)
red = redis.StrictRedis()

app.config['MONGODB_SETTINGS'] = {'db': 'chatchat', 'alias': 'default'}


def unix_to_datetime(x):
    return datetime.datetime.fromtimestamp(int(x)/1000000.0)
	
	
class DataBlock(Resource):
    def get(self, todo_id):
        print "i am here"
        return {todo_id: "None"}

    def post(self, todo_id):
        print 'i am in the post'

        return return_message, 201
		
@app.route('/event_listener/<tagID>')
@cross_origin(origins='*', methods=['GET', 'POST', 'OPTIONS'],
              headers=[
                'X-Requested-With', 'Content-Type', 'Origin',
                'withCredentials', 'Access-Control-Allow-Credentials',
                'token'])
def stream(tagID):
    resp = Response(event_stream(tagID), mimetype="text/event-stream")
    return resp

api.add_resource(DataBlock, '/<string:todo_id>')