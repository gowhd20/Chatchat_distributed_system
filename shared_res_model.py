####################################
## Readable code versus less code ##
####################################


from mongoengine import *
from web_server.general_api import general_api as api


class CommentModel(Document):
    by = StringField(max_length=128, required=True)
    timestamp = DateTimeField(default=api._get_current_time(), 
        required=True)
    comment = StringField(max_length=5000, default="")
    session_id = StringField(max_length=128)
    nid = StringField(max_length=128)


#class CommentListModel(Document):
#    comments = ListField(EmbeddedDocumentField(CommentDetailModel))


class ResourceManager(Document):
	accessed_by = StringField(max_length=128, required=True, primary_key=True)
	timestamp = DateTimeField(required=True)


class UserSessions(Document):
    created_at = DateTimeField(
        default=api._get_current_time(), 
        required=True)
    by = StringField(max_length=128)
    ssid = StringField(
        required=True,
        max_length=128, 
        default=api._generate_session_id())
    user_data = StringField(max_length=500, required=True)
    expiration = DateTimeField(required=True)
    modified = DateTimeField(required=True,
        default=api._get_current_time())




