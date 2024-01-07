# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/main/resources/cam1.yaml'

from lib.quicklock import lock
from sharp_eye.action import alert
from sharp_eye.rtspcam import RtspCamera
from sharp_eye.detector import MotionDetector
from sharp_eye.event_tracker import EventTracker
from sharp_eye.snapshot_tracker import SnapshotTracker

if __name__ == '__main__':
    lock()
    cam = RtspCamera()
    snapshot_tracker = SnapshotTracker()
    event_tracker = EventTracker(on_alert=alert, snapshot_tracker=snapshot_tracker)
    detector = MotionDetector(camera=cam, event_tracker=event_tracker, snapshot_tracker=snapshot_tracker)
    detector.run()
