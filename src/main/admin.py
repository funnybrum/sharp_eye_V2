"""
Sharp Eye main app.

The app consist of several parts:

1) The web server that exposes:
  a) Gallery with motion videos.
  b) UI for starting/stopping the motion detection for each camera.
  c) Security System UI for arming and disarming zones.
2) Motion detection processes for each camera that:
  a) Start ffmpeg process in the background responsible for tapping into the camera RTSP stream and generating frames.
  b) Basic motion detection logic that filters out frames with no motion.
  c) Event tracker responsible for identifying valid motion sequences.
  d) Motion sequence processor that uses ffmpeg to compress series of frames into video file.

There is external system that processes the motion sequences in order to detect objects in them and generate
notifications if persons or animals are detected.
"""
# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/main/resources/admin.yaml'

from admin.lib import Server
# Import the application routes
from admin.view import (  # noqa
    home,
    login,
    camera,
    hss,
    gallery
)
from admin.hss import (  # noqa
    bell,
    perimeter_partition
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
