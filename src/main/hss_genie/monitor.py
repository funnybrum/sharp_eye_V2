import os

from hss_genie import scheduler

from paho.mqtt.client import Client, MQTTv311

from lib import config
from lib.log import log
from lib.hss import HssZoneState
from lib.notifier_client import send_notification

PARTITION_STATE = {

}

mqtt_client = Client(
    client_id="master_mind_" + os.urandom(10).hex(),
    clean_session=True,
    protocol=MQTTv311)


def process_partition_state_change(partition, key, value):
    if key == "current_state":
        state = HssZoneState.from_string(value)

        if partition in PARTITION_STATE:
            if PARTITION_STATE[partition]['state'] == state:
                return
        else:
            PARTITION_STATE[partition] = {
                'state': state
            }

        PARTITION_STATE[partition]['state'] = state
        message = "Partition %s is %s" % (partition, state)
        send_notification(message, None, "arm_disarm")


ZONE_OPEN_EVENTS = {
    'sensor_motion': {
        'zones': ["Zone_041", "SERVICE_ROOM", "SERVICE_ROOM_ENT"],
        'message': "Motion on external zone: %s"
    },
    'sensor_motion_int': {
        'zones': ["ENTRY_DOOR", "ENTRY_HALLWAY", "HALLWAY_2", "HALLWAY_1", "STAIRS"],
        'message': "Motion on internal zone: %s"
    }
}


def process_zone_open(zone, key, value):
    if "True" == value:
        for event in ZONE_OPEN_EVENTS:
            if zone in ZONE_OPEN_EVENTS[event]['zones']:
                message = ZONE_OPEN_EVENTS[event]['message'] % zone
                send_notification(message, None, event)
                break


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))
    topic = message.topic

    if topic.startswith("paradox/states/partitions"):
        partition = topic.split("/")[3]
        key = topic.split("/")[4]
        if key.startswith("current_state"):
            process_partition_state_change(partition, key, payload)

    if topic.startswith("paradox/states/zones"):
        zone = topic.split("/")[3]
        key = topic.split("/")[4]
        if key == "open":
            process_zone_open(zone, key, payload)
        # log("Zone %s, key %s, payload %s" % (zone, key, payload))


@scheduler.scheduled_job('cron', id='mqtt_client_check_genie', minute='*')
def mqtt_client_check():
    if not mqtt_client.is_connected():
        log("Connecting MQTT client")
        mqtt_client.connect(config["mqtt"]["host"], config["mqtt"]["port"])
        mqtt_client.subscribe("paradox/states/partitions/#")
        mqtt_client.subscribe("paradox/states/zones/#")
        mqtt_client.on_message = on_message
        mqtt_client.loop_start()
