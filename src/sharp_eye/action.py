from io import BytesIO
import cv2

from lib import config
from lib.tools import send_email


def on_motion(motion_frame, snapshot, prev_snapshot, data):
    """
    Callback invoked when motion is detected.
    """

    if data['last_no_motion'] and data['motion_length'] == 1:
        mf = {
            'data': BytesIO(cv2.imencode('.jpg', motion_frame)[1].tostring()),
            'name': 'motion.jpg'}
        f = {
            'data': BytesIO(cv2.imencode('.jpg', cv2.resize(snapshot, (0, 0), fx=0.25, fy=0.25))[1].tostring()),
            'name': 'snapshot.jpg'}
        pf = {
            'data': BytesIO(cv2.imencode('.jpg', cv2.resize(prev_snapshot, (0, 0), fx=0.25, fy=0.25))[1].tostring()),
            'name': 'prev_snapshot.jpg'}

        subject = 'Motion @ home'
        text = 'Got motion on %s' % config['identifier'] + '\n' + str(data)

        # send_email(subject, text, [pf, f, mf])
