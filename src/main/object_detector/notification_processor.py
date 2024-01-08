from io import BytesIO
import cv2

import numpy

from lib import config
from lib.notifier_client import send_notification as _send_notification


class NotificationProcessor(object):
    def __init__(self):
        self._objects_of_interest = config['notifications']['objects']
        self._scale_factor = config['notifications']['snapshot']['scale']
        pass

    def _pick_best_frame(self, frames_with_objects):
        # Pick the frame with highest confidence sum
        frame_score = []
        for f in frames_with_objects:
            score = 0
            for obj in f['objects']:
                if obj['name'] in self._objects_of_interest:
                    obj_type = obj['name']
                    confidence = obj['confidence']
                    if confidence > self._objects_of_interest[obj_type]['threshold']:
                        score += confidence
            frame_score.append(score)

        best_frame_score = numpy.max(frame_score)
        if best_frame_score <= 0:
            # No objects of interest detected.
            return None

        return frames_with_objects[numpy.argmax(frame_score)]

    def process(self, video_file, frames_with_objects):
        notification_frame = self._pick_best_frame(frames_with_objects)
        if not notification_frame:
            return
        self._send_notification(notification_frame)

    def _send_notification(self, frame):
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

        topic = self._get_notification_topic(frame)

        message = "Motion detected: "
        for o in frame['objects']:
            message += "%s(%0.2f), " % (o['name'], o['confidence'])
        message = message[:-2] + '.'

        _send_notification(message, image, topic)
        # For debugging purposes - show frames instead of sending them through the notification service.
        # cv2.imshow(message, cv2.resize(frame['frame'], (0, 0), fx=0.5, fy=0.5))
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def _get_notification_topic(self, frame):
        confidence_name_pairs = [(o['confidence'], o['name']) for o in frame['objects']]
        sorted_pairs = sorted(confidence_name_pairs, key=lambda p: p[0], reverse=True)
        sorted_obj_types = [p[1] for p in sorted_pairs]
        for obj_type in sorted_obj_types:
            if obj_type in self._objects_of_interest:
                return self._objects_of_interest[obj_type]['topic']
