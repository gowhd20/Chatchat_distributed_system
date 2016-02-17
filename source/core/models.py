import datetime
from flask import url_for
from mongoengine import *


class CortexDocument(object):
    created_at = ComplexDateTimeField(default=datetime.datetime.now)
    uid = ObjectIdField()

    def get_absolute_url(self):
        return url_for('get', kwargs={"uid": self.uid})


class Person(Document, CortexDocument):
    """
    Signifies a real life person. A person should not exist more that once.
    Duplicate Users might be used later on as a fraud detection method.
    """
    first_names = StringField(max_length=255, required=True)
    last_names = StringField(max_length=255, required=True)
    signature_name = StringField(max_length=255, required=True)
    date_of_birth = DateTimeField(required=True)
    email = EmailField()

    def __unicode__(self):
        return self.signature_name

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'uid'],
        'ordering': ['-created_at']
    }


class DataBlock(Document, CortexDocument):
    """
    Contains a data chunck per second.
    """
    # this timestamp referes to the timestamp of the
    # device colecting the data

    source_timestamp = ListField(ComplexDateTimeField())
    channel_name = StringField()
    channel_type = StringField()
    data = ListField(FloatField())

    def __unicode__(self):
        return "%s-%s" % (self.channel_name, self.channel_type)

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'uid'],
        'ordering': ['-created_at']
        }
