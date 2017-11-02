#!/usr/bin/env python3
"""
  RPI Temperature and Humidity sensors application

  Copyright 2017 Visible Energy Inc. All Rights Reserved.
"""

import time
import json
import subprocess
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
  except Exception as e:
      print (e)
      return "{\"msg\":\"Invalid command.\"}"

def _get_identity():
    ret = {}
    try:
        ret["type"] = device_type
        ret["platform"] = Identity.platform
        ret["os"] = subprocess.Popen("uname -a", shell=True, stdout=subprocess.PIPE).stdout.read().decode()
        return json.dumps(ret)
    except Exception as e:
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
    rht.read();
    ret["temp"] = rht.t
    ret["hum"] = rht.rh
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
    print ('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
#    msg.payload = msg.payload.translate(None, '\\')
    # Decode JSON request
    data = json.loads(msg.payload.decode())

    # 1. received a message as result of a shared attribute request 
    # (since we subscribed to "v1/devices/me/attributes/response/+" at the time of connection)
    # this is the response to a device request to read one or more shared attributes
    # Received message example: {"shared":{"telemetry_period":30}}
    if 'shared' in data:
        # server attribute
        print ("received shared attributes")
        if 'telemetry_period' in data['shared']:
            print ("received telemetry period", data['shared']['telemetry_period'])
            _set_telemetry(data['shared']['telemetry_period'])
        return

    # 2. received a shared attribute update
    # (since we subscribed to "v1/devices/me/attributes" at the time of connection)
    # this is triggered by a shared attribute changing value (from an app or the device itself) 
    # Received message example: {"telemetry_period":15}
    if 'telemetry_period' in data:
        print ("received telemetry_period update", data['telemetry_period'])
        _set_telemetry(data['telemetry_period'])
        return

    # 3. only RPC requests from this point below
    # (since we subscribed to "v1/devices/me/rpc/request/+" at the time of connection)
    # scanning different methods that are implemented by the device
    if not 'method' in data:
        return

    # Check RPC request method
    #
    # Received RPC request: {"method":"getIdentity","params":{}}
    if data['method'] == 'getIdentity':
        # Reply with info object
        ret = _get_identity()
        print (ret)
        # return the response publishing to the proper topic
        client.publish(msg.topic.replace('request', 'response'), ret, 1)

    # Received RPC request: {"method":"getReadings","params":{}}
    if data['method'] == 'getReadings':
        # Reply with info object
        ret = _get_readings()
        print (ret)
        # return the response publishing to the proper topic
        client.publish(msg.topic.replace('request', 'response'), ret, 1)

# mqtt object
client = mqtt.Client()
# register callbacks
client.on_connect = on_connect
client.on_message = on_message

# use the device token as mqtt username with no password
#
# the device token is the key for the server ito dentify the device
# all subsequent uses of the client mqtt object are associated to this device
client.username_pw_set(device_token, password=None)
# connect to telesio mqtt
client.connect(mqtt_server, 1883, 60)  # no SSL
# start the mqtt parallel thread
client.loop_start()

# send device-side attributes to the server
# device-side attributes can only be written or changed by the device
attributes = {}
attributes["type"] = device_type
attributes["status"] = "OK"
#
# publising the device-side attributes: {"type":"RPI-TH", "status":"OK"}
# the status may become "KO" in case for instance a sensor gives error or disconnected
# the topic "v1/devices/me/attributes" is common to all devices
client.publish("v1/devices/me/attributes", json.dumps(attributes))

# request shared attributes 
# shared attributes can be written by the server or the device
# typically contain configuration parameters that may change but not frequently
client.publish("v1/devices/me/attributes/request/1", '{"sharedKeys":"telemetry_period"}')
# the on_message callback is called asynchronously when the server returns the response
# include "sharedKeys" for all the desired attributes of the device: {"sharedKeys":"key1, key2"}

in_error = False
ret = {}
while True:
    rht.read();
    ret["temp"] = rht.t
    ret["hum"] = rht.rh
    now = time.time()
    # send periodic data by publishing to the telemetry topic    
    client.publish("v1/devices/me/telemetry", json.dumps(ret))
    print (int (now), json.dumps(ret))

    # updating the device attribute status
    # this is really just to show that the status needs to be updated
    attributes = {}
    attributes["status"] = "OK"         # always ok in this device (but not elsewhere)
    # publish to the attributes topic to propagate the new status to the server
    client.publish("v1/devices/me/attributes", json.dumps(attributes))
    # both for telemetry and attributes updates an application may receive these
    # updates with the HTTP and WebSockets API and not using mqqt subscribe

    time.sleep(telemetry_interval - (time.time() - now))
