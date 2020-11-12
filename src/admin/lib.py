from __future__ import absolute_import

import hashlib
from time import time
from lib import config
from flask import Flask


def generate_session_token():
    return hashlib.sha256(bytes(config['password'], encoding="utf-8") + bytes(str(time()), encoding="utf-8"))\
        .hexdigest()

state = {}
for cam in config['cameras']:
    state[cam] = {}
    for prop in ['active']:
        state[cam][prop] = config[cam][prop]
state['alarm'] = False

server_webapp = Flask(config['identifier'])
