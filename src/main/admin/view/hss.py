from flask import render_template

from admin import server_webapp
from admin.view.login import requires_auth


@server_webapp.route('/hss')
@requires_auth
def get_hss():
    return render_template('hss.html')
