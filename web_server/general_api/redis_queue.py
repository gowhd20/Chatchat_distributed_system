####################################
## Readable code versus less code ##
####################################


import redis

r = redis.StrictRedis()

class Queue(object):
	""" FIFO queue """
	def __init__(self):
		self.space_name = "queue:%s" %(r.incr("queue_space"))


	def push(self, ele):
		print self.space_name
		push_element = r.lpush(self.space_name, ele)


	def pop(self):
		print self.space_name
		return r.rpop(self.space_name)


	def size(self):
		return r.dbsize()


	def flush(self):
		return r.flushall()


	def exists(self):
		return r.exists(self.space_name)

