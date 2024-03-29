import os

from time import time, sleep
from threading import Thread

from paho.mqtt.client import Client, MQTTv311

from lib import config
from lib.log import log

from admin import scheduler


class Bell(Thread):
    def __init__(self, loop_interval=0.2):
        Thread.__init__(self)
        self._running = True
        self._loop_interval = loop_interval
        self._mqtt_client = Client(
            client_id="master_mind_" + os.urandom(8).hex(),
            clean_session=True,
            protocol=MQTTv311)
        self._is_bell_on = None
        self._bell_end_ts = 0

    def _check_client(self):
        if not self._mqtt_client.is_connected():
            log("Connecting MQTT client")
            self._mqtt_client.connect(config["mqtt"]["host"], config["mqtt"]["port"])
            self._mqtt_client.loop_start()

    def run(self):
        log("Starting the bell controlling thread")
        start = time()
        while self._running:
            self.loop()
            while self._running and time() < start + self._loop_interval:
                sleep(0.1)
            start += self._loop_interval

    def loop(self):
        self._check_client()
        now = time()

        if (now > self._bell_end_ts and self._is_bell_on == True) or self._is_bell_on is None:
            self._mqtt_client.publish('paradox/control/outputs/5', "off")
            self._is_bell_on = False

        if now <= self._bell_end_ts and self._is_bell_on == False:
            self._mqtt_client.publish('paradox/control/outputs/5', "on")
            self._is_bell_on = True

    def alert(self, duration_seconds):
        self._bell_end_ts = time() + duration_seconds
        self.loop()

    def silence(self):
        self._bell_end_ts = time() - 1
        self.loop()


_bell = Bell()


@scheduler.task('cron', id='bell_check', minute='*')
def _bell_check():
    global _bell
    if _bell is None or not _bell.is_alive():
        _bell = Bell()
        _bell.start()


def trigger_sound_alert(duration_seconds):
    _bell_check()
    _bell.alert(duration_seconds)


def silence_alert():
    _bell_check()
    _bell.silence()