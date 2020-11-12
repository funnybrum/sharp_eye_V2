# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/resources/cam1.yaml'

from lib.quicklock import lock
from sharp_eye.action import on_motion
from sharp_eye.rtspcam import RtspCamera
from sharp_eye.detector import MotionDetector


if __name__ == '__main__':
    lock()
    cam = RtspCamera()
    detector = MotionDetector(camera=cam, on_motion=on_motion)
    detector.run()
