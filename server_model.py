import datetime
from flask import url_for
from mongoengine import *

## default app document info
class ChatchatDocument(object):
    created_at = ComplexDateTimeField(default=datetime.datetime.now(), required=True)
    uid = StringField(max_length=255, required=True, primary_key=True)

    def get_absolute_url(self): 
        return url_for('get', kwargs={"uid": self.uid})


## [BEGIN] Server database schema 
class ChildrenModel(EmbeddedDocument):
    uid = StringField(max_length=255, required=True, primary_key=True)
    created_at = DateTimeField(default=datetime.datetime.now(), required=True)
    public_key = StringField(max_length=500, required=True)
    timestamp_last_access = DateTimeField(default=datetime.datetime.now())

    meta = {
        'indexes': ['-created_at', 'uid'],
        'ordering': ['-created_at'],
        'title': 'children',
        'slug': 'app clients are here, contains different restricted info from AppModel'
    }


class ServerLogModel(EmbeddedDocument):
    timestamp_logged = DateTimeField(default=datetime.datetime.now(), required=True)
    log = StringField(default="It's a wonderful day", max_length=1000)

    meta = {
        'indexes': ['-timestamp_logged'],
        'ordering': ['-timestamp_logged'],
        'title': 'server log',
    }


class WebServerModel(Document, ChatchatDocument):
    public_key = StringField(max_length=500, required=True)
    private_key = StringField(max_length=1000, required=True)
    public_key_c = StringField(max_length=500, required=True)
    private_key_c = StringField(max_length=1000, required=True)
    server_log = ListField(EmbeddedDocumentField(ServerLogModel))
    children = ListField(EmbeddedDocumentField(ChildrenModel))

    def __unicode__(self):
        return self.uid

    meta = {
        'indexes': ['-created_at', 'uid'],
        'ordering': ['-created_at'],
        'title': 'Web server',
        'slug': 'This is the web server where all the clients get together'
    }
## [END]

