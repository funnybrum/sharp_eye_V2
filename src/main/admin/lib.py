from threading import Thread

from flask import Flask
from flask_apscheduler import APScheduler

from lib import config


def gen_state():
    state = {}
    for cam in config['cameras']:
        state[cam] = {}
        for prop in ['active']:
            state[cam][prop] = config[cam][prop]
    return state


server_webapp = Flask(config['identifier'])
scheduler = APScheduler()
state = gen_state()


class Server(Thread):
    _instance = None

    def __init__(self):
        super(Server, self).__init__()
        self.setDaemon(True)

    def run(self):
        """ Run the server."""
        scheduler.api_enabled = False
        scheduler.init_app(server_webapp)
        scheduler.start()

        server_webapp.run(debug=False, host=config['host'], port=config['port'], threaded=True)

    @classmethod
    def startup(cls):
        """ Start the server in a thread and return. """
        if not Server._instance:
            Server._instance = Server()

        if not Server._instance.isAlive():
            super(Server, Server._instance).start()
