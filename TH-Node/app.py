#!/usr/bin/env python3
"""
  RPI Temperature and Humidity sensors application

  Copyright 2017 Visible Energy Inc. All Rights Reserved.
"""

import time
import json
import subprocess
import RPi.GPIO as GPIO
from HIH6130.io import HIH6130
import paho.mqtt.client as mqtt
from config import Identity

# Device configuration
device_type = Identity.device_type
device_token = Identity.device_token
# Device shared attribute
telemetry_interval = 15     # default value

# FQDN MQTT broker
mqtt_server = "service.telesio.io"

# HIH6130 temperature and humidity sensor
rht = HIH6130()

def _rexec(params):
  """Start a subprocess shell to execute the specified command and return its output.

  params - a one element list ["/bin/cat /etc/hosts"]
  """
  # check that params is a list
  if not isinstance(params, list) or len(params) == 0:
     return "Parameter must be a not empty list"    
  command = params[0]
  try:
      subprocess.check_call(command,shell=True)
      out = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()
      return json.dumps(out.decode())
  except Exception, e:
      print e
      return "{\"msg\":\"Invalid command.\"}"

def _get_identity():
    ret = {}
    try:
        ret["type"] = device_type
        ret["platform"] = Identity.platform
        ret["os"] = subprocess.Popen("uname -a", shell=True, stdout=subprocess.PIPE).stdout.read().decode()
        return json.dumps(ret)
    except Exception, e:
        return "{\"error\":\"" + e + "\"}"

def _set_telemetry(params):
    global telemetry_interval
    telemetry_interval = params
    ret = {}
    ret["telemetry"] = telemetry_interval
    return json.dumps(ret)

def _get_readings():
    ret = {}
    ret["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    return json.dumps(ret)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # subscribe to the RPC channel
    client.subscribe("v1/devices/me/rpc/request/+")
    # subscribe to attributes updates
    client.subscribe("v1/devices/me/attributes")
    # subscribe to attributes responses
    client.subscribe("v1/devices/me/attributes/response/+")

# callback for PUBLISH messages received from the server
def on_message(client, userdata, msg):    
    print 'Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload)
    msg.payload = msg.payload.translate(None, '\\')
    # Decode JSON request
    data = json.loads(msg.payload)

    # received an attribute update/response --  Message: {"shared":{"telemetry_period":30}}
    if 'shared' in data:
        # server attribute
        print "received shared attributes"
        if 'telemetry_period' in data['shared']:
            print "received telemetry period", data['shared']['telemetry_period']
            _set_telemetry(data['shared']['telemetry_period'])
        return

    # received a client attribute update -- Message: {"telemetry_period":15}
    if 'telemetry_period' in data:
        print "received telemetry_period update", data['telemetry_period']
        _set_telemetry(data['telemetry_period'])
        return

    # only RPC from this point below
    if not 'method' in data:
        return

    # Check RPC request method
    #

    # RPC Message: {"method":"getIdentity","params":{}}
    if data['method'] == 'getIdentity':
        # Reply with info object
        ret = _get_term_info()
        print ret
        client.publish(msg.topic.replace('request', 'response'), ret, 1)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# use the device token as mqtt username with no password
client.username_pw_set(device_token, password=None)
# connect to telesio mqtt
client.connect(mqtt_server, 1883, 60)  # no SSL
# start the mqtt thread
client.loop_start()

# send device attributes to the server
attributes = {}
attributes["type"] = device_type
attributes["status"] = "OK"
client.publish("v1/devices/me/attributes", json.dumps(attributes))

# request shared attributes
client.publish("v1/devices/me/attributes/request/1", '{"sharedKeys":"telemetry_period"}')

in_error = False
ret = {}
while True:
    rht.read(); 
    ret["temp"] = rht.t
    ret["hum"] = rht.rh
    now = time.time()
    client.publish("v1/devices/me/telemetry", json.dumps(ret))
    print int (now), json.dumps(ret)

    attributes = {}
    attributes["status"] = "OK"
    client.publish("v1/devices/me/attributes", json.dumps(attributes))

    time.sleep(telemetry_interval - (time.time() - now))
