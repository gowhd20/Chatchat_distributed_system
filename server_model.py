####################################
## Readable code versus less code ##
####################################


from mongoengine import *
from web_server.general_api import general_api as api
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict


## default app document info
class ChatchatDocument(object):
    created_at = ComplexDateTimeField(default=api._get_current_time(), 
        required=True)
    sid = StringField(max_length=255, required=True, primary_key=True)

    def get_absolute_url(self): 
        return url_for('get', kwargs={"sid": self.sid})


## [BEGIN] Server database schema 
class ChildrenModel(EmbeddedDocument):
    nid = StringField(max_length=255, required=True, primary_key=True)
    ## @Note, datetime needs to be switched to local datetime, this is UTC
    created_at = DateTimeField(default=api._get_current_time(), 
        required=True)
    public_key = StringField(max_length=500, required=True)
    last_work = DateTimeField()
    last_access = DateTimeField(default=api._get_current_time(),
        required=True)

    meta = {
        'indexes': ['-created_at', 'sid'],
        'ordering': ['-created_at'],
        'title': 'children',
        'slug': 'app clients are here, contains different restricted info from AppModel'
    }


class ServerLogModel(EmbeddedDocument):
    by = StringField(max_length=255, required=True)
    timestamp = DateTimeField(default=api._get_current_time(), 
        required=True)
    header = StringField(default="today", max_length=500)
    log = StringField(default="It's a wonderful day", max_length=1000)

    meta = {
        'indexes': ['-timestamp_logged'],
        'ordering': ['-timestamp_logged'],
        'title': 'server log',
    }


class WebServerModel(Document, ChatchatDocument):
    public_key = StringField(max_length=500, required=True)
    private_key = StringField(max_length=1000, required=True)
    common_key_public = StringField(max_length=500, required=True)
    common_key_private = StringField(max_length=1000, required=True)
    last_access_to_res = StringField(max_length=255)
    server_log = ListField(EmbeddedDocumentField(ServerLogModel))
    children = ListField(EmbeddedDocumentField(ChildrenModel))

    def __unicode__(self):
        return self.sid

    meta = {
        'indexes': ['-created_at', 'sid'],
        'ordering': ['-created_at'],
        'title': 'Web server'
    }


class Sessions(Document):
    created_at = DateTimeField(default=api._get_current_time(), 
        required=True)
    by = StringField(max_length=128)
    ssid = StringField(required=True,
        max_length=128, 
        default=api._generate_session_id())
    user_data = StringField(max_length=500, required=True)
    expiration = DateTimeField(required=True)
    modified = DateTimeField(default=api._get_current_time())


##  users' session manager
class MongoSession(CallbackDict, SessionMixin):

    def __init__(self, 
        initial=None, 
        ssid=None, 
        modified=None):

        CallbackDict.__init__(self, initial)
        self.ssid = ssid
        self.modified = modified


class MongoSessionInterface(SessionInterface):

    def __init__(self, host='localhost', port=27017,
                 db='', collection='sessions', by=None):
        #client = MongoClient(host, port)
        self.sessions = Sessions._get_collection()  #client[db][collection]
        self.by = by


    def open_session(self, app, request):
        ssid = request.cookies.get(app.session_cookie_name)
        if ssid:
            stored_session = self.sessions.find_one({'ssid': ssid})
            #print "matched_session {}".format(stored_session)
            """
            if stored_session:
                if stored_session.get('expiration') > api._get_current_time():
                    print "session id not expired: {}".format(ssid)

                    return MongoSession(
                        initial=stored_session['user_data'], 
                        ssid=stored_session['ssid'])"""

        ssid = api._generate_session_id()
        print "new ssid: {}".format(ssid)
        return MongoSession(ssid=ssid)


    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)

        if not session:
            ## in web_server session is not defined
            print "delete cookies"      
            response.delete_cookie(app.session_cookie_name, domain=domain)
            return
        if self.get_expiration_time(app, session):
            expiration = self.get_expiration_time(app, session)
        else:
            expiration = api._get_expiration_time()
            print "expiration has been extended {}".format(expiration)

        self.sessions.update_one(
                          {'ssid': session.ssid},
                          {
                               '$set':{
                               'by':self.by,
                               'ssid': session.ssid,
                               'user_data': session,
                               'expiration': expiration,
                               'modified':api._get_current_time()
                               }
                           }, upsert=True)      ## upsert true

        res = self.sessions.find()
        for r in res:
            print str(r) + "sessions"

        response.set_cookie(app.session_cookie_name,
                            session.ssid,
                            expires=self.get_expiration_time(app, session),
                            httponly=True, domain=domain)
## [END]

