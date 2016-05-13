####################################
## Readable code versus less code ##
####################################


from mongoengine import *
from web_server.general_api import general_api as api


class CommentDetailModel(EmbeddedDocument):
    by = StringField(max_length=128, required=True, primary_key=True)
    timestamp = DateTimeField(default=api._get_current_time(), 
        required=True)
    comment = StringField(max_length=5000, default="")


class CommentListModel(Document):
    comments = ListField(EmbeddedDocumentField(CommentDetailModel))


class ResourceManager(Document):
	accessed_by = StringField(max_length=128, required=True, primary_key=True)
	timestamp = DateTimeField(required=True)


class SharedSessions(Document):
    created_at = DateTimeField(default=api._get_current_time(), 
        required=True)
    by = StringField(max_length=128)
    ssid = StringField(required=True,
        max_length=128, 
        default=api._generate_session_id())
    user_data = StringField(max_length=500, required=True)
    expiration = DateTimeField(required=True)
    modified = DateTimeField()




