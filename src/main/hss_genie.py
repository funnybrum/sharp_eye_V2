# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/main/resources/hss.yaml'

from time import sleep

from lib.quicklock import lock

from hss_genie import scheduler
from hss_genie.monitor import mqtt_client_check_genie

if __name__ == '__main__':
    try:
        lock()
    except RuntimeError:
        exit(0)

    scheduler.start()
    mqtt_client_check_genie()

    while True:
        sleep(5)

