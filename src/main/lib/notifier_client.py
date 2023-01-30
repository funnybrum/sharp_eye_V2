import requests

from . import config


def send_notification(message):
    payload = {
        'event': "camera_motion",
        'message': {
            'text': message
        }
    }
    cookies = {
        'auth_token': config['notifier']['token']
    }
    requests.post(config['notifier']['url'], json=payload, cookies=cookies)
