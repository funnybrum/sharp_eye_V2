from __future__ import absolute_import

from subprocess import Popen

from lib import config
from lib.log import log
from admin import state
from lib.quicklock import (
    is_locked,
    force_unlock
)
from time import sleep


def check():
    for cam in config['cameras']:
        cam_state = state[cam]
        is_running = is_locked(cam)
        should_be_running = cam_state['active']
        if is_running != should_be_running:
            if should_be_running:
                log('Arming %s' % cam)
                Popen(config[cam]['command'], shell=True)
            else:
                log('Disarming %s' % cam)
                force_unlock(cam)
            sleep(5)
