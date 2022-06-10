from functools import wraps
from flask import (
    request,
    redirect,
    make_response,
    render_template
)

from admin import server_webapp
import hashlib
from time import time
from lib import config


def generate_session_token():
    return hashlib.sha256(bytes(config['password'], encoding="utf-8") + bytes(str(time()), encoding="utf-8"))\
        .hexdigest()


session_token = generate_session_token()


def requires_auth(f):
    """Wrapper for routes that requires auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        global session_token
        no_session_token = request.cookies.get('session_id') != session_token

        print(no_session_token, request.args.get("key"))
        if no_session_token and request.args.get("key") == config["secret_key"]:
            session_token = generate_session_token()
            response = make_response(redirect('/'))
            response.set_cookie('session_id', value=session_token)
            return response

        if no_session_token:
            return login()

        return f(*args, **kwargs)
    return decorated


@server_webapp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        if str(request.form['password']) == str(config['password']):
            global session_token
            session_token = generate_session_token()
            response = make_response(redirect('/'))
            response.set_cookie('session_id', value=session_token)
            return response
        return redirect('/')


@server_webapp.route('/logout')
@requires_auth
def logout():
    global session_token
    session_token = generate_session_token()
    return redirect('/')
