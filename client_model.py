####################################
## Readable code versus less code ##
####################################


from mongoengine import *
from web_server.general_api import general_api as api

## default app document info
class ChatchatDocument(object):
    created_at = ComplexDateTimeField(default=api._get_current_time(), 
        required=True)
    nid = StringField(max_length=255, required=True, primary_key=True)

    def get_absolute_url(self): 
        return url_for('get', kwargs={"nid": self.nid})


class NodeModel(EmbeddedDocument):
    nid = StringField(max_length=255, required=True, primary_key=True)
    public_key = StringField(max_length=500)

    meta = {
        'indexes': ['nid'],
        'ordering': ['nid'],
        'title': 'nodes',
        'slug': 'other app clients are here'
    }


## [BEGIN] app clinet database schema
## this data chunk should not be used by web server
## idealy this schema should be seperate from other schemas  
class AppModel(Document, ChatchatDocument):
    master_sid = StringField(max_length=255)
    public_key = StringField(max_length=500, required=True)
    server_public_key = StringField(max_length=500)
    common_key_private = StringField(max_length=1000)
    private_key = StringField(max_length=1000, required=True)
    last_access_to_res = DateTimeField()
    last_work = DateTimeField()
    last_access = DateTimeField(default=api._get_current_time(), 
        required=True)
    nodes = ListField(EmbeddedDocumentField(NodeModel))

    def __unicode__(self):
        return self.nid

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'nid'],
        'ordering': ['-created_at'],
        'title': 'About new app client',
        'slug': 'A new user joins in'
    }

## [END]