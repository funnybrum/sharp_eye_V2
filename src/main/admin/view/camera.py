import cv2
import os
import io
from datetime import datetime
from flask import (
    send_file,
    abort,
    redirect,
    render_template
)

from lib import config
from admin import (
    state,
    server_webapp
)
from admin.view.login import requires_auth


@server_webapp.route('/cameras')
@requires_auth
def get_cameras():
    return render_template('cameras.html', state=state, config=config)


@server_webapp.route('/view/<cam_id>')
@requires_auth
def get_camera_snapshot(cam_id):
    if cam_id not in config['cameras']:
        return abort(404)
    return render_template('snapshot.html', img='/snapshot/%s' % cam_id)


@server_webapp.route('/snapshot/<cam_id>')
@requires_auth
def get_camera_snapshot_image(cam_id):
    if cam_id not in config['cameras']:
        return abort(404)

    img = cv2.imread(config[cam_id]['snapshot'])
    stamp = os.path.getmtime(config[cam_id]['snapshot'])
    stamp = datetime.fromtimestamp(stamp)
    stamp = stamp.strftime('%H:%M:%S')
    cv2.putText(img, stamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 255, 128), 2)

    _, jpeg = cv2.imencode('.jpg', img)

    return send_file(io.BytesIO(jpeg.tostring()), mimetype='image/%s' % config[cam_id]['snapshot'][-3:])


@server_webapp.route('/arm/<cam_id>')
@requires_auth
def get_camera_arm(cam_id=None):
    if cam_id in config['cameras']:
        state[cam_id]['active'] = True
    return redirect('/cameras')


@server_webapp.route('/disarm/<cam_id>')
@requires_auth
def get_camera_disarm(cam_id=None):
    if cam_id in config['cameras']:
        state[cam_id]['active'] = False
    return redirect('/cameras')
