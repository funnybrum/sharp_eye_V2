import cv2
from io import BytesIO
from time import time

import numpy

from lib import config
from lib.log import log
from lib.notifier_client import send_notification as _send_notification


class NotificationProcessor(object):
    def __init__(self):
        self._objects_of_interest = config['notifications']['objects']
        self._scale_factor = config['notifications']['snapshot']['scale']
        self._last_message_to_topic_ts = {}
        self._topic_suppression_time = config['notifications']['topic_suppression']

    def _pick_best_frame(self, scores, frames_with_objects):
        if not scores:
            return None, None

        object_type_of_interest = max(scores, key=scores.get)
        object_score = scores[object_type_of_interest]

        if object_type_of_interest not in self._objects_of_interest or \
                object_score < self._objects_of_interest[object_type_of_interest]['threshold']:
            return None, None

        # Find the frame with the highest confidence score for the object of interest.
        best_score = 0
        best_frame = None
        for f in frames_with_objects:
            frame_score = sum([obj['confidence'] for obj in f['objects'] if obj['name'] == object_type_of_interest])
            if frame_score > best_score:
                best_score = frame_score
                best_frame = f

        return object_type_of_interest, best_frame

    def process(self, video_file, frames_with_objects, scores):
        object_name, notification_frame = self._pick_best_frame(frames_with_objects, scores)
        if not notification_frame:
            return
        self._send_notification(object_name, notification_frame)

    def _send_notification(self, obj_type, frame):
        # Draw rectangle in the frame to mark the object of interest. Used for dev purposes.
        for obj in frame['objects']:
            cv2.rectangle(
                frame['frame'],
                (int(obj['xmin']), int(obj['ymin'])),
                (int(obj['xmax']), int(obj['ymax'])),
                (0, 255, 0),
                2
            )

        # Encode the image to JPEG format and convert it to bytes. The image is scaled down to reduce the payload size.
        image = BytesIO(
            cv2.imencode('.jpg',
                         cv2.resize(frame['frame'],
                                    (0, 0),
                                    fx=self._scale_factor, fy=self._scale_factor))
            [1].tostring())

        topic = self._objects_of_interest[obj_type]['topic']

        message = "Motion detected: "
        for o in frame['objects']:
            message += "%s(%0.2f), " % (o['name'], o['confidence'])
        message = message[:-2] + '.'

        log(message)

        if not self._is_topic_suppressed(topic):
            _send_notification(message, image, topic)
        self._register_topic_event(topic)

        # For debugging purposes - show frames instead of sending them through the notification service.
        # cv2.imshow(message, cv2.resize(frame['frame'], (0, 0), fx=0.5, fy=0.5))
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def _is_topic_suppressed(self, topic):
        if topic not in self._last_message_to_topic_ts:
            return False
        if time() - self._last_message_to_topic_ts[topic] > self._topic_suppression_time[topic]:
            return False
        return True

    def _register_topic_event(self, topic):
        self._last_message_to_topic_ts[topic] = time()
