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

last_alarm_state = False


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

    global last_alarm_state
    if state['alarm'] != last_alarm_state:
        last_alarm_state = state['alarm']
        if last_alarm_state:
            log('Activating alarm')
        else:
            log('Deactivating alarm')
