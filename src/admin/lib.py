from __future__ import absolute_import

import ssl

from flask import Flask
from threading import Thread

from lib import config


def gen_state():
    state = {}
    for cam in config['cameras']:
        state[cam] = {}
        for prop in ['active']:
            state[cam][prop] = config[cam][prop]
    state['alarm'] = False
    return state


server_webapp = Flask(config['identifier'])
state = gen_state()


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
        server_webapp.run(debug=False, host=config['host'], port=config['port'], ssl_context=ssl_context, threaded=True)

    @classmethod
    def startup(cls):
        """ Start the server in a thread and return. """
        if not Server._instance:
            Server._instance = Server()

        if not Server._instance.isAlive():
            super(Server, Server._instance).start()
