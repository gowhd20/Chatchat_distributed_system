import redis



red = redis.StrictRedis()


def event_stream(channel):
    print "am i called?"
    pubsub = red.pubsub()
    pubsub.subscribe(channel)
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        print message['data']
        yield 'data: %s\n\n' % message['data']


def raw_event_stream(channel):
    pubsub = red.pubsub()
    pubsub.subscribe(channel)
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        yield message['data']
