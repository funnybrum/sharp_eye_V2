import os

from time import sleep

from flask import render_template
from flask import (
    abort,
    redirect
)
from paho.mqtt.client import Client, MQTTv311

from lib import config
from lib.log import log
from lib.hss import HssZoneState
from admin.view.login import requires_auth
from admin import (
    server_webapp,
    scheduler
)


class HssMode:
    AUTO = "auto"
    MANUAL = "manual"


HSS_STATE = {
    "1ST_FLOOR": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Floor 1"
    },
    "2ND_FLOOR": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Floor 2"
    },
    "SERVICE_ROOM": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Service room"
    },
    "WORKSHOP": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Workshop"
    }
}

mqtt_client = Client(
    client_id="master_mind_" + os.urandom(8).hex(),
    clean_session=True,
    protocol=MQTTv311)


@server_webapp.route('/hss')
@requires_auth
def get_hss():
    return render_template('hss.html', hss_state=HSS_STATE)


@server_webapp.route('/hss/control/<partition>/<action>', methods=['GET'])
@requires_auth
def get_hss_control_partition_action(partition, action):
    if partition not in HSS_STATE or action not in ['arm', 'disarm', HssMode.AUTO, HssMode.MANUAL]:
        return abort(403)

    if action in ['arm', 'disarm']:
        mqtt_client.publish('paradox/control/partitions/%s' % partition, action)
        sleep(2)

    if action in [HssMode.MANUAL, HssMode.AUTO]:
        HSS_STATE[partition]['mode'] = action

    return redirect('/hss')


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))
    topic = message.topic

    partition = topic.split("/")[3]
    key = topic.split("/")[4]
    if key == "current_state":
        HSS_STATE[partition]['state'] = HssZoneState.from_string(payload)


@scheduler.task('cron', id='mqtt_client_check_admin', minute='*')
def mqtt_client_check():
    if not mqtt_client.is_connected():
        log("Connecting MQTT client")
        mqtt_client.connect(config["mqtt"]["host"], config["mqtt"]["port"])
        mqtt_client.subscribe("paradox/states/partitions/#")
        mqtt_client.on_message = on_message
        mqtt_client.loop_start()
