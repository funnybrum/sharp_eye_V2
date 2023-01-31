from io import BytesIO
import cv2

from lib import config
from lib.log import log
from lib.notifier_client import send_notification


def alert(frame):
    """
    Callback for sending an alert.
    """
    thresholds = config['notifications']['threshold']
    if thresholds['pixels'] > frame.non_zero_pixels or thresholds['percent'] > frame.non_zero_percent:
        log("Skipping notification for %s" % frame.get_metadata())
        return

    image = BytesIO(cv2.imencode('.jpg', cv2.resize(frame.get_motion_frame(), (0, 0), fx=0.25, fy=0.25))[1].tostring())
    text = 'Got motion on %s' % config['identifier']

    send_notification(text, image)
