import os

from time import time, sleep
from threading import Thread

from lib.log import log
from lib.hss import HssZoneState

from admin import scheduler
from admin.hss import HSS_STATE, PERIMETER_PARTITION
from admin.hss.bell import trigger_sound_alert, silence_alert


class PerimeterPartition(Thread):
    _ACTIVATION_TIMEOUT = 120

    def __init__(self, loop_interval=1):
        Thread.__init__(self)
        self._running = True
        self._loop_interval = loop_interval
        self._bell_end_ts = 0
        self._motion_events_ts = []
        self._current_event_series_warned = False

    def run(self):
        log("Starting the perimeter partition controlling thread")
        start = time()
        while self._running:
            self.loop()
            while self._running and time() < start + self._loop_interval:
                sleep(0.1)
            start += self._loop_interval

    def loop(self):
        now = time()
        self._motion_events_ts = [ts for ts in self._motion_events_ts if now - ts < self._ACTIVATION_TIMEOUT]

        if HSS_STATE[PERIMETER_PARTITION]['state'] == HssZoneState.ARMED:
            if len(self._motion_events_ts) == 0:
                self.reset_events()
            elif len(self._motion_events_ts) == 1 and not self._current_event_series_warned:
                # beep
                trigger_sound_alert(0.2)
                self._current_event_series_warned = True
            elif len(self._motion_events_ts) > 1:
                # This will re-trigger until there is no motion for the activation timeout.
                trigger_sound_alert(2)


    def register_motion(self):
        self._motion_events_ts.append(time())

    def reset_events(self):
        self._motion_events_ts = []
        self._current_event_series_warned = False


_perimeter_partition = PerimeterPartition()


@scheduler.task('cron', id='perimeter_partition_check', minute='*')
def _perimeter_partition_check():
    global _perimeter_partition
    if _perimeter_partition is None or not _perimeter_partition.is_alive():
        _perimeter_partition = PerimeterPartition()
        _perimeter_partition.start()


def register_motion():
    _perimeter_partition_check()
    _perimeter_partition.register_motion()


def arm():
    _perimeter_partition_check()
    _perimeter_partition.reset_events()
    HSS_STATE[PERIMETER_PARTITION]['state'] = HssZoneState.ARMED


def disarm():
    _perimeter_partition_check()
    HSS_STATE[PERIMETER_PARTITION]['state'] = HssZoneState.DISARMED
