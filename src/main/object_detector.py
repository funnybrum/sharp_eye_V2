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
from lib.metadata_store import MetadataStore
from object_detector.orchestrator import Orchestrator
from object_detector.yolo import Detector
from object_detector.notification_processor import NotificationProcessor
from object_detector.perimeter_partition_processor import PerimeterPartitionProcessor

if __name__ == '__main__':
    try:
        lock()
    except RuntimeError:
        exit(0)

    detector = Detector()
    detector.init()
    log("Models loaded.")

    notification_processor = NotificationProcessor()
    perimeter_partition_processor = PerimeterPartitionProcessor()
    metadata_store = MetadataStore()

    orchestrator = Orchestrator(
        detector=detector,
        metadata_store=metadata_store,
        processors=[perimeter_partition_processor, notification_processor]
    )

    log("Starting object detection.")

    # Trigger video file scan every 300 seconds or if the trigger file is availabe.
    trigger_filename = config['object_detection']['trigger_file']
    count = 0
    while True:
        if os.path.exists(trigger_filename):
            os.remove(trigger_filename)
            count += 9999
        else:
            count += 1
        if count > 300:
            while orchestrator.loop() > 0:
                sleep(1)
            count = 0
        sleep(1)
