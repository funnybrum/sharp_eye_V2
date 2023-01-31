# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/main/resources/admin.yaml'

from admin.lib import Server
# Import the application routes
from admin.view import (  # noqa
    login,
    camera,
    gallery
)
import admin.supervisor as supervisor
from lib.quicklock import lock
from time import sleep

if __name__ == '__main__':
    try:
        lock()
    except RuntimeError:
        exit(0)
    Server.startup()
    while True:
        supervisor.check()
        sleep(1)
