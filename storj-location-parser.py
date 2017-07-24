import time
import json
import re
import Geohash
import datetime
import Queue
import os

from urllib2 import urlopen
from urllib2 import HTTPError
from influxdb import InfluxDBClient


#The nodeID to be monitored
NODE_ID = "23c20fc08ec5c1c23696b46daf0600d1c58170bc"

#INFLUXDB details
INFLUXDB_DATABASE = "renter_monitoring"
INFLUXDB_ADDRESS = "192.168.0.15"
INFLUXDB_PORT = 8086
INFLUXDB_ADMIN = "root"
INFLUXDB_PASSWORD = "root"

#max number of "received valid message from" which are going to be buffered
MAX_MESSAGES_BUFFER_SIZE = 30

#string constants
RECEIVED_VALID_MESSAGE = "received valid message from "
CONSIGNMENT_MESSAGE = "handling storage consignment request from "


# get location string (lat,long) from an ip address
# uses http://ipinfo.io/ which has a limit of 1.000 requests per day
# cant read dynddns
def getLocationFromIP(ip):
    try:
        url = "http://ipinfo.io/" + ip + "/json"
        response = urlopen(url)
        data = json.load(response)
        if "loc" in data:
            return data["loc"]
        else:
            return -1
    except HTTPError:
        return -1

def parseReceivedValidMessageLine(log_line):
    #load json from line
    line_json = json.loads(log_line)
    substring = line_json["message"].split("received valid message from ")[1]

    #load json from message
    message_json = json.loads(substring)

    #get location from message_json
    location = getLocationFromIP(message_json["address"])

    #dynddns cant be read with getLocationFromIP
    if location is not -1:
        lat,lng = location.split(",")
        ghash = Geohash.encode(float(lat), float(lng), precision=7)

        result = {}
        result["timestamp"] = line_json["timestamp"]
        result["nodeID"] = message_json["nodeID"]
        result["ip"] = message_json["address"]
        result["ghash"] = ghash

        return result
    else:
        return ""


def sendToInfluxdb(buffered_messages):
    for i in range(buffered_messages.qsize()):
        json_body = [
            {
                "measurement": "renters",
                "tags": {
                    "host": NODE_ID,
                    "node": buffered_messages.queue[i]["nodeID"],
                    "geohash": buffered_messages.queue[i]["ghash"],
                    "ip": buffered_messages.queue[i]["ip"]
                },
                "time": buffered_messages.queue[i]["timestamp"],
                "fields": {
                    "value": 1
                }
            }
        ]

        client = InfluxDBClient(INFLUXDB_ADDRESS, INFLUXDB_PORT, INFLUXDB_ADMIN, INFLUXDB_PASSWORD, INFLUXDB_DATABASE)
        client.write_points(json_body)



# ---------------------------
# Main
# ---------------------------

#buffer the last "received valid message from" messages
buffered_messages = Queue.Queue(MAX_MESSAGES_BUFFER_SIZE)

#get current date
currentDate = '{d.year}-{d.month}-{d.day}'.format(d=datetime.datetime.now())
file = open(NODE_ID + "_" + currentDate + ".log","r")
while 1:
    where = file.tell()
    line = file.readline()
    if not line:
        time.sleep(1)
        file.seek(where)
    else:
        if RECEIVED_VALID_MESSAGE in line:
            message = parseReceivedValidMessageLine(line)

            if message is not "":
                buffered_messages.put(parseReceivedValidMessageLine(line))

                if buffered_messages.full():
                    sendToInfluxdb(buffered_messages)
                    buffered_messages.queue.clear()
    testdate = '{d.year}-{d.month}-{d.day}'.format(d=datetime.datetime.now())
    if currentDate != testdate and os.path.exists(NODE_ID + "_" + testdate + ".log"):
        currentDate = testdate
        file.close()
        file = open(NODE_ID + "_" + currentDate + ".log","r")
