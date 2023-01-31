import requests
import uuid

from . import config


def send_notification(message, image):
    service_url = config['notifier']['url']
    auth_token = config['notifier']['token']
    image_name = "%s.jpg" % str(uuid.uuid4())

    upload_url = "%s/image?auth_token=%s" % (service_url, auth_token)
    requests.put(upload_url, files={image_name: image})

    payload = {
        'event': "camera_motion",
        'message': {
            'text': message,
            'image': image_name,
            'thumbnail': True
        }
    }

    push_url = "%s/push?auth_token=%s" % (service_url, auth_token)
    requests.post(push_url, json=payload)
