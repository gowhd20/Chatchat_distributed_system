####################################
## Readable code versus less code ##
####################################


import redis

class Queue(object):
	""" FIFO queue """
	def __init__(self, db=0):
		self.r = redis.StrictRedis(db=db)
		self.space_name = "queue:%s" %(self.r.incr("queue_space"))


	def push(self, value):
		return self.r.lpush(self.space_name, value)
		 

	def custom_push(self, name, value):
		return self.r.lpush(name, value)


	def pop(self):
		return self.r.rpop(self.space_name)


	def custom_pop(self, name):
		return self.r.rpop(name)


	def length(self):
		return self.r.llen(self.space_name)


	def custom_len(self, name):
		return self.r.llen(name)


	def flush(self):
		return self.r.flushall()


	def exists(self):
		return self.r.exists(self.space_name)


	def append(self, key, value):
		return self.r.append(key, value)


	def get(self, key):
		return self.r.get(key)


	def delete(self, key):
		return self.r.delete(key)


	def bottom(self):
		return self.r.lindex(self.space_name, self.length()-1)


	def get_custom_list(self, name):
		return self.r.lrange(name, 0, self.custom_len(name)-1)


	def get_list(self):
		return self.r.lrange(self.space_name, 0, self.length()-1)


	def save(self):
		return self.r.bgsave()



### deprecated #######################
class CustomQueue(object):
	def __init__(self, db=1):
		self.r = redis.StrictRedis(db=db)


	def push(self, key, value):
		print "custom queue, push accessed"
		return self.r.lpush(key, value)


	def pop(self, key):
		print "custom queue, pop accessed"
		return self.r.rpop(key)


	def size(self):
		return self.r.dbsize()


	def flush(self):
		return self.r.flushall()


	def exists(self):
		return self.r.exists(self.space_name)
