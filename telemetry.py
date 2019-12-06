#!/usr/bin/python

from sense_hat import SenseHat, ACTION_PRESSED, ACTION_RELEASED
from itertools import cycle
from signal import pause
import threading
import datetime
import time
import jwt
import paho.mqtt.client as mqtt

class Spinner(object):
    spinners = cycle(('-', '/', '|', '\\'))
    def __init__(self):
        self.stop_running = threading.Event()
        threading.Thread(target=self.init_spin).start()
    def stop(self):
        self.stop_running.set()
    def init_spin(self):
        while not self.stop_running.is_set():
            sense.show_letter(next(self.spinners), text_colour=color)
            time.sleep(0.08)

def pushed_any(event):
    global spinner, color, sense
    if event.action == ACTION_PRESSED:
        sense.show_letter("X")
    if event.action == ACTION_RELEASED:
        color = (0,0,255)
        spinner = Spinner()
        sense.stick.direction_any = None
        connect()

def connect():
    global client, spinner, color
    client = mqtt.Client(client_id=_CLIENT_ID)
    client.username_pw_set(
        username='whatever',
        password=create_jwt())
    client.on_connect = on_connect
    client.on_disconnect=on_disconnect
    client.on_message = on_message
    client.tls_set(ca_certs=root_cert_filepath)
    for i in range(3):
        try:
            client.connect('mqtt.googleapis.com', 8883)
            client.loop_start()
        except Exception as e:
            spinner.stop()
            sense.clear(255,0,0)
            with open('/home/pi/GCP_Quick_Starts/telemetry.log', 'a+') as logf:
                logf.write(str(datetime.datetime.now()) + "---" + str(e))
            time.sleep(5)
            color = (0,0,255)
            spinner = Spinner()
            continue
        else:
            break

def create_jwt():
    cur_time = datetime.datetime.utcnow()
    token = {
        'iat': cur_time,
        'exp': cur_time + datetime.timedelta(minutes=60),
        'aud': project_id
    }
    with open(ssl_private_key_filepath, 'r') as f:
        private_key = f.read()
    return jwt.encode(token, private_key, ssl_algorithm)

def on_connect(unusued_client, unused_userdata, unused_flags, rc):
    global color, client, payload, prev_temperature
    color = (0,255,0)
    print(str(datetime.datetime.now()) + '--- on_connect ({}:{})'.format(rc, mqtt.error_string(rc)))
    client.subscribe(_MQTT_COMMANDS_TOPIC, qos=0)
    #client.subscribe(_MQTT_CONFIG_TOPIC, qos=0)
    curr_temperature = sense.get_temperature()
    payload = '{{"ts":{}, "project_id":"{}", "gcp_location":"{}", "registryId":"{}", "deviceId":"{}", "prev_temperature":"{}", "curr_temperature":"{}"}}'. \
            format(int(time.time()), project_id, gcp_location, registry_id, device_id, prev_temperature, curr_temperature)
    prev_temperature = curr_temperature
    print('Publishing: ' + payload)
    client.publish(_MQTT_TELEMETRY_TOPIC, payload, qos=0)
    payload = None

def on_message(unused_client, unused_userdata, message):
    global spinner, sense, client
    spinner.stop()
    msg = message.payload.decode('utf-8')
    print(str(datetime.datetime.now()) + ' --- Received message "{}" on topic "{}"'.format(msg, message.topic))
    if msg == 'red':
        sense.clear(255,0,0)
    elif msg == 'green':
        sense.clear(0,255,0)
    elif msg == 'blue':
        sense.clear(0,0,255)
    else:
        sense.show_letter('?')
    time.sleep(1)
    sense.clear()
    client.disconnect()

def on_disconnect(unused_client, unused_userdata, rc):
    global client, sense
    print(str(datetime.datetime.now()) + ' --- on_disconnect ({}:{})\n'.format(rc, mqtt.error_string(rc)))
    client.loop_stop()
    client = None
    sense.stick.direction_any = pushed_any

sense = SenseHat()
sense.low_light = True

ssl_private_key_filepath = '######'
ssl_algorithm = 'RS256' # Either RS256 or ES256
root_cert_filepath = '######'
project_id = '######'
gcp_location = '######'
registry_id = '######'
device_id = '######'

_CLIENT_ID = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(project_id, gcp_location, registry_id, device_id)
_MQTT_TELEMETRY_TOPIC = '/devices/{}/events'.format(device_id)
_MQTT_STATE_TOPIC = '/devices/{}/state'.format(device_id)
_MQTT_CONFIG_TOPIC = '/devices/{}/config'.format(device_id)
_MQTT_COMMANDS_TOPIC = '/devices/{}/commands/#'.format(device_id)

prev_temperature = 0
payload = None
client = None
spinner = None
color = (0,0,255)
sense.stick.direction_any = pushed_any
pause()
