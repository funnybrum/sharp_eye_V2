from __future__ import absolute_import

import ssl
import cv2
import os
import io
from datetime import datetime
from threading import Thread
from functools import wraps
from flask import (
    send_file,
    abort,
    request,
    redirect,
    make_response,
    render_template
)

from lib import config
from admin import (
    state,
    server_webapp
)
from admin.lib import generate_session_token


class Server(Thread):
    _instance = None

    def __init__(self):
        super(Server, self).__init__()
        self.setDaemon(True)

    def run(self):
        """ Run the server."""
        # logging.getLogger('werkzeug').setLevel(logging.ERROR)
        ssl_context = None
        if 'ssl_key' in config:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            ssl_context.load_cert_chain(config['ssl_cert'], config['ssl_key'], config['ssl_pass'])
        server_webapp.run(debug=False, host=config['host'], port=config['port'], ssl_context=ssl_context)

    @classmethod
    def startup(cls):
        """ Start the server in a thread and return. """
        if not Server._instance:
            Server._instance = Server()

        if not Server._instance.isAlive():
            super(Server, Server._instance).start()


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


@server_webapp.route('/')
@requires_auth
def status():
    return render_template('home.html', state=state, config=config)


@server_webapp.route('/view/<cam_id>')
@requires_auth
def view(cam_id):
    if cam_id not in config['cameras']:
        return abort(404)
    return render_template('snapshot.html', img='/snapshot/%s' % cam_id)


@server_webapp.route('/snapshot/<cam_id>')
@requires_auth
def snapshot(cam_id):
    if cam_id not in config['cameras']:
        return abort(404)

    img = cv2.imread(config[cam_id]['snapshot'])
    stamp = os.path.getmtime(config[cam_id]['snapshot'])
    stamp = datetime.fromtimestamp(stamp)
    stamp = stamp.strftime('%H:%M:%S')
    cv2.putText(img, stamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 255, 128), 2)

    _, jpeg = cv2.imencode('.jpg', img)

    return send_file(io.BytesIO(jpeg.tostring()), mimetype='image/%s' % config[cam_id]['snapshot'][-3:])
    # return send_file(config[cam_id]['snapshot'], mimetype='image/%s' % config[cam_id]['snapshot'][-3:])


@server_webapp.route('/arm/<cam_id>')
@requires_auth
def arm(cam_id=None):
    if cam_id in config['cameras']:
        state[cam_id]['active'] = True
    return redirect('/')


@server_webapp.route('/disarm/<cam_id>')
@requires_auth
def disarm(cam_id=None):
    if cam_id in config['cameras']:
        state[cam_id]['active'] = False
    return redirect('/')


@server_webapp.route('/logout')
@requires_auth
def logout():
    global session_token
    session_token = generate_session_token()
    return redirect('/')


@server_webapp.route('/health')
def health_check():
    return 'OK'
