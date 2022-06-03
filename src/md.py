# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/resources/cam3.yaml'

from lib.quicklock import lock
from sharp_eye.action import alert
from sharp_eye.rtspcam import RtspCamera
from sharp_eye.detector import MotionDetector
from sharp_eye.event_tracker import EventTracker


if __name__ == '__main__':
    lock()
    cam = RtspCamera()
    event_tracker = EventTracker(on_alert=alert)
    detector = MotionDetector(camera=cam, event_tracker=event_tracker)
    detector.run()
