import datetime
from flask import url_for
from mongoengine import *

## default app document info
class ChatchatDocument(object):
    created_at = ComplexDateTimeField(default=datetime.datetime.now(), required=True)
    uid = StringField(max_length=255, required=True, primary_key=True)

    def get_absolute_url(self): 
        return url_for('get', kwargs={"uid": self.uid})

class NodeModel(EmbeddedDocument):
    uid = StringField(max_length=255, required=True, primary_key=True)
    public_key = StringField(max_length=500)

    meta = {
        'indexes': ['uid'],
        'ordering': ['uid'],
        'title': 'nodes',
        'slug': 'other app clients are here'
    }

## [BEGIN] app clinet database schema
## this data chunk should not be used by web server
## idealy this schema should be seperate from other schemas  
class AppModel(Document, ChatchatDocument):
    wsuid = StringField(max_length=255)
    public_key = StringField(max_length=500, required=True)
    server_public_key = StringField(max_length=500)
    private_key_c = StringField(max_length=1000)
    private_key = StringField(max_length=1000, required=True)
    is_token_holder = BooleanField(required=True, default=False)
    timestamp_last_token_hold = DateTimeField()
    timestamp_last_access = DateTimeField(default=datetime.datetime.now(), required=True)
    nodes = ListField(EmbeddedDocumentField(NodeModel))

    def __unicode__(self):
        return self.uid

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'uid'],
        'ordering': ['-created_at'],
        'title': 'About new app client',
        'slug': 'A new user joins in'
    }

## [END]