#!/usr/bin/python3
"""
This file is part of FF_SmsServer (https://github.com/FlyingDomotic/FF_SmsServer)

It reads received SMS through MQTT, analyze them and execute received commands through Domoticz

Traces are kept in a log file, rotated each week.

Author: Flying Domotic
License: GNU GPL V3
"""

fileVersion = "1.0.2"

import paho.mqtt.client as mqtt
import pathlib
import os
import socket
import random
import logging
import logging.handlers as handlers
import json
from datetime import datetime
from FF_analyzeCommand import FF_analyzeCommand

# Replace CR and LF by \r and \n in order to keep log lines structured
def replaceCrLf(message):
    return str(message).replace("\r","\\r").replace("\n","\\n")

# Executed when MQTT is connected
def on_connect(client, userdata, flags, rc):
        mqttClient.publish(MQTT_LWT_TOPIC, '{"state":"up", "version":"'+str(fileVersion)+'", "startDate":"'+str(datetime.now())+'"}', 0, True)
    mqttClient.subscribe(MQTT_RECEIVE_TOPIC, 0)
    mqttClient.subscribe(DOMOTICZ_OUT_TOPIC, 0)

# Executed when receiving a message from MQTT subscribed topics
def on_message(mosq, obj, msg):
    if msg.retain==0:
        payload = msg.payload.decode("UTF-8")
        try:
            jsonData = json.loads(payload)
        except:
            logger.exception(F"Can't decode >{replaceCrLf(msg.payload)} received from {msg.topic}")
            return
        # Is this a Domoticz out message?
        if msg.topic == DOMOTICZ_OUT_TOPIC:
            # Is this a Domoticz out message with our SMS answer device idx?
            if getValue(jsonData, 'idx') == DOMOTICZ_SMS_ANSWER_IDX:
                # Yes, get result code and log it
                logger.info(F"Answer is >{getValue(jsonData, 'svalue1')}<")
                return
        # Is this a SMS received message?
        elif msg.topic == MQTT_RECEIVE_TOPIC:
            # Extract number, date and message parts
            number = getValue(jsonData, 'number').strip()
            date = getValue(jsonData, 'date').strip()
            message = getValue(jsonData, 'message').strip()
            logger.info(F"Received >{replaceCrLf(message)}< from {number} at {date} on {msg.topic}")
            # All 3 must be defined
            if message == '' or date == '' or number == '':
                logger.error("Can't find 'number', 'date' or 'message'")
                return
        else:
            logger.error(F"Can't understand topic {msg.topic} with content {payload}")
                return
        # Check message prefix   
        if SMS_PREFIX == "" or analyzer.compare(message[:len(SMS_PREFIX)], SMS_PREFIX, 4):
            # Remove prefix
            message = message[len(SMS_PREFIX):].strip()
            logger.info(F"Message {replaceCrLf(message)}<")
            # Analyze message
            errorText, messages = analyzer.analyzeCommand(message)
            # Do we had an error analyzing command?
            if errorText != "":
                # Yes, log it and send error back to SMS sender
                logger.error(F"Error: {replaceCrLf(messages)}")
                # Compose SMS answer message
                message = errorText
                jsonAnswer = {}
                jsonAnswer['number'] = str(number)
                jsonAnswer['message'] = message
                answerMessage = json.dumps(jsonAnswer)
                logger.info(F"Answer: >{replaceCrLf(answerMessage)}<")
                mqttClient.publish(MQTT_SEND_TOPIC, answerMessage)
            else:
                # Analyzed without error
                if messages:
                    logger.info(F"Info: {replaceCrLf(messages)}")
                # Rebuild non abbreviated command
                understoodMessage = analyzer.command+" "+analyzer.deviceName+(" "+analyzer.valueToSet if analyzer.valueToSet != None else "")
                logger.info(F"Understood command is >{understoodMessage}<")
                # If defined, set Domoticz last received message with non abbreviated command
                if (DOMOTICZ_SMS_TEXT_IDX):
                    jsonMessage = '{"command":"udevice","idx":'+str(DOMOTICZ_SMS_TEXT_IDX)+',"nvalue":0,"svalue":"'+understoodMessage+'","rssi":6,"battery":255}'
                    mqttClient.publish(DOMOTICZ_IN_TOPIC, jsonMessage)
                # Prepare Domoticz SMS command message (space delimited)
                domoticzMessage = \
                    # SMS sender phone number
                    str(number)+ \
                    # Command value
                    " "+str(analyzer.commandValue)+ \
                    # Device ID
                    " "+str(analyzer.deviceId)+ \
                    # Device class
                    " "+str(analyzer.deviceClass)+ \
                    # Value to set as given
                    " "+str(analyzer.valueToSet)+ \
                    # Value to set remapped with "values" in "deviceClasses" of smsTables.json
                    " "+str(analyzer.valueToSetRemapped)
                logger.info(F"Domoticz message: >{domoticzMessage}<")
                # Format message in a Domoticz input MQTT topic format
                jsonMessage = '{"command":"udevice","idx":'+str(DOMOTICZ_SMS_MESSAGE_IDX)+',"nvalue":0,"svalue":"'+domoticzMessage+'","rssi":6,"battery":255}'
                # Push the message to Domoticz.
                #   An LUA script in Domoticz will read and execute it, sending answer to sender directly.
                #   A copy of this answer will be read in DOMOTICZ_OUT_TOPIC/DOMOTICZ_SMS_ANSWER_IDX and logged for information
                mqttClient.publish(DOMOTICZ_IN_TOPIC, jsonMessage)

# Executed when a topic is subscribed
def on_subscribe(mosq, obj, mid, granted_qos):
  pass

# Returns a dictionary value giving a key or default value if not existing
def getValue(dict, key, default=''):
    if key in dict:
        if dict[key] == None:
            return default #or None
        else:
            return dict[key]
    else:
        return default

#   *****************
#   *** Main code ***
#   *****************

# Set current working directory to this python file folder
currentPath = pathlib.Path(__file__).parent.resolve()
os.chdir(currentPath)

# Get this file name (w/o path & extension)
cdeFile = pathlib.Path(__file__).stem

# Get this host name
hostName = socket.gethostname()

### Here are settings to be adapted to your context ###

# SMS settings
SMS_PREFIX = "myPrefix"

# MQTT Settings
MQTT_BROKER = "*myMqttHost*"
MQTT_RECEIVE_TOPIC = "smsServer/received"
MQTT_SEND_TOPIC = "smsServer/toSend"
MQTT_LWT_TOPIC = "smsServer/LWT/"+hostName
MQTT_ID = "*myMqttUser*"
MQTT_KEY = "*myMqttKey*"

# Domoticz SMS command sensor idx
DOMOTICZ_SMS_MESSAGE_IDX = 9999
DOMOTICZ_SMS_ANSWER_IDX = 9998
DOMOTICZ_SMS_TEXT_IDX = 9997
DOMOTICZ_IN_TOPIC = "domoticz/in"
DOMOTICZ_OUT_TOPIC = "domoticz/out"

### End of settings ###

# Log settings
log_format = "%(asctime)s:%(levelname)s:%(message)s"
logger = logging.getLogger(cdeFile)
logger.setLevel(logging.INFO)
logHandler = handlers.TimedRotatingFileHandler(str(currentPath) + cdeFile +'_'+hostName+'.log', when='W0', interval=1)
logHandler.suffix = "%Y%m%d"
logHandler.setLevel(logging.INFO)
formatter = logging.Formatter(log_format)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.info(F"----- Starting on {hostName}, version {fileVersion} -----")

# Analyze SMS tables
decodeFile = os.path.join(currentPath, 'smsTables.json')
analyzer = FF_analyzeCommand()

errorText, messages = analyzer.loadData(decodeFile)

# Do we had errors?
if errorText:
    logger.error(F"Loading tables status: {messages}")
    exit(2)

logger.info("Loading tables status: ok")
if messages:
    logger.info(messages)

# Use this python file name and random number as client name
random.seed()
mqttClientName = pathlib.Path(__file__).stem+'_{:x}'.format(random.randrange(65535))

# Initialize MQTT client
mqttClient = mqtt.Client(mqttClientName)
mqttClient.on_message = on_message
mqttClient.on_connect = on_connect
mqttClient.on_subscribe = on_subscribe
mqttClient.username_pw_set(MQTT_ID, MQTT_KEY)
# Set Last Will Testament (QOS=0, retain=True)
mqttClient.will_set(MQTT_LWT_TOPIC, '{"state":"down"}', 0, True)
# Connect to MQTT (asynchronously to allow MQTT server not being up when starting this code)
mqttClient.connect_async(MQTT_BROKER)
# Never give up!
mqttClient.loop_forever()
