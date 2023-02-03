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
        "armed": True,
        "mode": HssMode.MANUAL,
        "properties": {},
        "name": "Floor 1"
    },
    "2ND_FLOOR": {
        "arm": False,
        "mode": HssMode.MANUAL,
        "properties": {},
        "name": "Floor 2"
    },
    "SERVICE_ROOM": {
        "armed": False,
        "mode": HssMode.MANUAL,
        "properties": {},
        "name": "Service room"
    },
    "WORKSHOP": {
        "armed": False,
        "mode": HssMode.MANUAL,
        "properties": {},
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

    if topic.startswith("paradox/states/partitions"):
        partition = topic.split("/")[3]
        if partition not in HSS_STATE:
            HSS_STATE[partition] = {
                "armed": False,
                "mode": HssMode.MANUAL,
                "properties": {}
            }
        key = topic.split("/")[4]
        if key.startswith("arm"):
            HSS_STATE[partition]['properties'][key] = payload == "True"
            HSS_STATE[partition]['armed'] = any(HSS_STATE[partition]['properties'].values())


def on_log(client, userdata, level, buff):
    log("%s: %s" % (mqtt_client.is_connected(), buff))


@scheduler.task('cron', id='mqtt_client_check_admin', minute='*')
def mqtt_client_check_admin():
    log("%s: %s" % (mqtt_client.is_connected(), "mqtt_client_check"))
    if not mqtt_client.is_connected():
        log("Connecting MQTT client")
        mqtt_client.connect(config["mqtt"]["host"], config["mqtt"]["port"])
        mqtt_client.subscribe("paradox/states/partitions/#")
        mqtt_client.on_message = on_message
        mqtt_client.on_log = on_log
        mqtt_client.loop_start()


mqtt_client_check()
