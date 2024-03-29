import os
if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/main/resources/admin.yaml'

from time import sleep

from flask import render_template
from flask import (
    abort,
    redirect,
    request
)
from paho.mqtt.client import Client, MQTTv311

from lib import config
from lib.log import log
from lib.hss import HssZoneState
from admin import (
    server_webapp,
    scheduler
)
from admin.hss import HSS_STATE, PERIMETER_PARTITION, HssMode
from admin.hss.bell import (
    trigger_sound_alert,
    silence_alert
)
from admin.hss.perimeter_partition import (
    register_motion,
    arm,
    disarm
)
from admin.view.login import requires_auth


mqtt_client = Client(
    client_id="master_mind_" + os.urandom(8).hex(),
    clean_session=True,
    protocol=MQTTv311)


@server_webapp.route('/hss')
@requires_auth
def get_hss():
    return render_template('hss.html', hss_state=HSS_STATE)


@server_webapp.route('/hss/control/partition/<partition>/<action>', methods=['GET'])
@requires_auth
def get_hss_control_partition_action(partition, action):
    if partition not in HSS_STATE or action not in ['arm', 'disarm', HssMode.AUTO, HssMode.MANUAL]:
        return abort(403)

    if action in ['arm', 'disarm']:
        if partition not in [PERIMETER_PARTITION]:
            mqtt_client.publish('paradox/control/partitions/%s' % partition, action)
            sleep(0.5)
        else:
            # This is the perimeter partition
            if action == 'arm':
                arm()
            else:
                disarm()

    if action in [HssMode.MANUAL, HssMode.AUTO]:
        HSS_STATE[partition]['mode'] = action

    return redirect('/hss')


@server_webapp.route('/hss/control/alarm/<action>', methods=['GET'])
@requires_auth
def get_hss_control_alarm_action(action):
    if action not in ['on', 'off']:
        return abort(403)

    if action == 'on':
        duration = request.args.get("duration", 1)
        # import pdb; pdb.set_trace()
        trigger_sound_alert(float(duration))
        print(float(duration))
    elif action == 'off':
        silence_alert()
        pass

    return redirect('/hss')


@server_webapp.route('/hss/control/motion', methods=['GET'])
def get_hss_control_motion():
    register_motion()
    return ''

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
