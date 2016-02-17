from flask import Blueprint, render_template
from flask.views import MethodView
from source.core.models import Person, DataBlock

import json

# FIXME - Propper path to templates
user_blueprint = Blueprint('user', __name__,
                             template_folder='../templates/',
                             static_folder='../static',)
							 

class ListView(MethodView):
    def get(self):
        people = Person.objects.all()
        return render_template('user/list.html', people=people,
                               page='user')



# Register the urls
user_blueprint.add_url_rule('/', view_func=ListView.as_view('list'))

