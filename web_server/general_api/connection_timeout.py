####################################
## Readable code versus less code ##
####################################

import threading
from web_server.general_api import general_api as api

logger = api.__get_logger('ConnTimeout.run')


class ConnTimeout(object):
    def __init__(self, timeout, function, servers=5, args=[], kwargs=[]):
        self.timeout = timeout
        self.timer = None   #threading.Timer(timeout, pickle.loads(function), args)
        self.count = 0
        self.f = function
        self.servers = servers
        self.args = args
        self.kwargs = kwargs
        super(ConnTimeout, self).__init__()


    #def __reduce__(self):
    #    return (self.__class__, (self.name, self.address))


    def start(self):
        return self._start()


    def _start(self):
        self.timer = threading.Timer(self.timeout, self._handler)
        self.timer.start()


    def is_alive(self):
        return self._is_alive()


    def _is_alive(self):
        if self.timer:
            return self.timer.is_alive()
        else:
            return self.timer


    def _handler(self):
        if self.count<self.servers:
            self.count+=1
        else:
            self.count=0
        
        ## recursive timer call
        self.timer = threading.Timer(self.timeout, self._handler)
        self.timer.start()
        
        args = self.args[:]
        args.append(api.MN_RKEY+str(self.count))
        logger.info(" trying to connect to "+api.MN_RKEY+str(self.count))

        self.f(*args)
        del args[:]


    def stop(self):
        if self.timer.is_alive():
            self.timer.cancel()
            logger.info("timer killed...")
            return True
        return False


## other approach, didn't like that has to keep the main thread running by force
## using while inside main
##  http://code.activestate.com/recipes/496800-event-scheduling-threadingtimer/
"""
import thread
import threading

class Operation(threading._Timer):
    def __init__(self, *args, **kwargs):
        threading._Timer.__init__(self, *args, **kwargs)

    def run(self):
        while True:
            self.finished.clear()
            self.finished.wait(self.interval)
            if not self.finished.isSet():
                self.function(*self.args, **self.kwargs)
            else:
                return
            self.finished.set()

class Manager(object):

    def add_operation(self, operation, interval, args=[], kwargs={}):
        self.op = Operation(interval, operation, args, kwargs)
        thread.start_new_thread(self.op.run, ())

    def cancel(self):
        if self.op:
            self.op.cancel()

if __name__ == '__main__':
    # Print "Hello World!" every 5 seconds
    
    import time

    def hello():
        print "Hello World!"

    timer = Manager()
    timer.add_operation(hello, 5)

    while True:
        time.sleep(.1)
"""
