import redis

config = {
    'host': 'localhost',
    'port': 1380,
    'db': 0,
}

r = redis.StrictRedis()