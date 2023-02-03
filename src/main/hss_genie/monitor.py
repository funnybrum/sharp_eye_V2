import os

from hss_genie import scheduler

from paho.mqtt.client import Client, MQTTv311

from lib import config
from lib.log import log


mqtt_client = Client(
    client_id="master_mind_" + os.urandom(10).hex(),
    clean_session=True,
    protocol=MQTTv311)


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))
    topic = message.topic

    if topic.startswith("paradox/states/partitions"):
        partition = topic.split("/")[3]
        key = topic.split("/")[4]
        if key.startswith("arm"):
            pass
            # log("Partition %s, topic %s, payload %s" % (partition, topic, payload))

    if topic.startswith("paradox/states/zones"):
        zone = topic.split("/")[3]
        key = topic.split("/")[4]
        # log("Zone %s, key %s, payload %s" % (zone, key, payload))


@scheduler.scheduled_job('cron', id='mqtt_client_check_genie', minute='*')
def mqtt_client_check_genie():
    if not mqtt_client.is_connected():
        log("Connecting MQTT client")
        mqtt_client.connect(config["mqtt"]["host"], config["mqtt"]["port"])
        mqtt_client.subscribe("paradox/states/partitions/#")
        mqtt_client.subscribe("paradox/states/zones/#")
        mqtt_client.on_message = on_message
        mqtt_client.loop_start()
