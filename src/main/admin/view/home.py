from flask import render_template

from admin import server_webapp
from admin.view.login import requires_auth


@server_webapp.route('/')
@requires_auth
def get_home():
    return render_template('home.html')
