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

    def _pick_best_frame(self, frames_with_objects):
        # Find the object with highest confidence score
        score_sum = {}
        for f in frames_with_objects:
            for obj in f['objects']:
                obj_name = obj['name']
                obj_confidence = obj['confidence']
                if obj_name in self._objects_of_interest or \
                   obj_confidence >= self._objects_of_interest[obj_name]['threshold']:
                    if not obj_name in score_sum:
                        score_sum[obj_name] = 0
                    score_sum[obj_name] += obj_confidence

        if not score_sum:
            return None, None

        top_object = max(score_sum, key=score_sum.get)

        # Pick the frame with highest confidence sum for the top object
        frame_score = []
        for f in frames_with_objects:
            score = 0
            for obj in f['objects']:
                if obj['name'] == top_object:
                    score += obj['confidence']
            frame_score.append(score)

        return top_object, frames_with_objects[numpy.argmax(frame_score)]

    def process(self, video_file, frames_with_objects):
        object_name, notification_frame = self._pick_best_frame(frames_with_objects)
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
