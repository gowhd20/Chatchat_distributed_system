import redis
import logging 
import sys

config = {
	'host' : 'localhost',
	'port' : 6379,
	'db'   : 0,
}
logging.warning('are we here?')


red = redis.StrictRedis()


def event_stream(channel):
    print "am i called?"
    pubsub = red.pubsub()
    pubsub.subscribe(channel)
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        yield 'data: %s\n\n' % message['data']


def raw_event_stream(channel):
    pubsub = red.pubsub()
    pubsub.subscribe(channel)
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        yield message['data']
