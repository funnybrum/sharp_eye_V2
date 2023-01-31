from io import BytesIO
import cv2

from lib import config
from lib.notifier_client import send_notification


def alert(frame):
    """
    Callback for sending an alert.
    """
    # mf = {
    #     'data': BytesIO(cv2.imencode('.jpg', cv2.resize(frame.get_motion_frame(), (0, 0), fx=0.25, fy=0.25))[1].tostring()),
    #     'name': 'motion.jpg'}
    f = {
        'data': BytesIO(cv2.imencode('.jpg', cv2.resize(frame.frame, (0, 0), fx=0.5, fy=0.5))[1].tostring()),
        'name': 'snapshot.jpg'}
    # pf = {
    #     'data': BytesIO(cv2.imencode('.jpg', cv2.resize(frame.prev_frame, (0, 0), fx=0.5, fy=0.5))[1].tostring()),
    #     'name': 'prev_snapshot.jpg'}

    text = 'Got motion on %s' % config['identifier'] + '\n' + str(frame.get_metadata())

    send_notification(text, f['data'])
    # send_email(subject, text, [mf, f, pf])
