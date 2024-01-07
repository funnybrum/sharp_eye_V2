"""
ML based object detection.

Input is based on the frames with detected motion coming from the Sharp Eye. Split as separate process
for reducing the complexity of the Sharp Eye app.

Outputs are:
 1) Notifications for detected objects
 2) Metadata for the video gallery
"""
# Temporary, for test purposes
import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/main/resources/object_detector.yaml'

from time import sleep

from lib import config
from lib.log import log
from lib.quicklock import lock
from object_detector.orchestrator import Orchestrator
from object_detector.yolo import Detector
from object_detector.notification_processor import NotificationProcessor

if __name__ == '__main__':
    try:
        lock()
    except RuntimeError:
        exit(0)

    # Prepare the input folder.
    input_path = config['object_detection']['path']
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    else:
        # Clean up old data.
        for f in os.listdir(input_path):
            os.remove(os.path.join(input_path, f))

    detector = Detector()
    detector.init()
    log("Models loaded.")

    notification_processor = NotificationProcessor()

    orchestrator = Orchestrator(
        detector=detector,
        processors=[notification_processor]
    )

    log("Starting object detection.")

    while True:
        orchestrator.loop()
        sleep(1)
