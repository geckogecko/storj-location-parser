import time
import json
import re
import Geohash
import datetime
import Queue
import os
import requests

from influxdb import InfluxDBClient
from influxdb import SeriesHelper

#The nodeID to be monitored
NODE_ID = "3217206e6e00c336ddf164a0ad88df7f22c8891b"

#Path to your storj log folder
LOG_FOLDER_PATH = "/home/georg/storj-location-parser/"

#INFLUXDB details
INFLUXDB_DATABASE = "renter_monitoring"
INFLUXDB_ADDRESS = "173.212.220.3"
INFLUXDB_PORT = 8086
INFLUXDB_ADMIN = "root"
INFLUXDB_PASSWORD = "root"

#max number of "received valid message from" which are going to be buffered
MAX_MESSAGES_BUFFER_SIZE = 30

#string constants
RECEIVED_VALID_MESSAGE = "received valid message from "
CONSIGNMENT_MESSAGE = "handling storage consignment request from "
BLACKLIST_STORJ_BRIDGE = "renters.prod.storj.io"
BLACKLIST_STORJ_TUNNEL = "storj.dk"
BLACKLIST_LOOPBACK_IP = "127.0.0.1"

# get location string (lat,long) from an ip address
# uses http://freegeoip.net/ which has a limit of 15.000 requests per hour
# cant read dynddns
def getGhashFromIP(ip):
    url = "http://freegeoip.net/json/" + ip
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        if "latitude" in data and "longitude" in data:
            return Geohash.encode(float(data['latitude']), float(data['longitude']), precision=7)
    elif response.status_code == 203:
        #limit of 15.000 reached implement fallback here
        return -1
    else:
        return -1


def parseReceivedValidMessageLine(log_line):
    #load json from line
    line_json = json.loads(log_line)
    substring = line_json["message"].split("received valid message from ")[1]

    #load json from message
    message_json = json.loads(substring)

    #get location from message_json
    ghash = getGhashFromIP(message_json["address"])

    #dynddns cant be read with getLocationFromIP
    if ghash is not -1:
        result = {}
        result["timestamp"] = line_json["timestamp"]
        result["nodeID"] = message_json["nodeID"]
        result["ip"] = message_json["address"]
        result["ghash"] = ghash

        if result["ip"] == BLACKLIST_LOOPBACK_IP:
            return -1

        return result
    else:
        return ""

def sendToInfluxdb(buffered_messages):

    myClient = InfluxDBClient(INFLUXDB_ADDRESS, INFLUXDB_PORT, INFLUXDB_ADMIN, INFLUXDB_PASSWORD, INFLUXDB_DATABASE)

    class mySeriesHelper(SeriesHelper):
	class Meta:
	    client = myClient
	    series_name = 'renters'
	    time = ['time']
	    fields = ['value']
	    tags = ['host', 'node', 'geohash', 'ip']
	    bulk_size = MAX_MESSAGES_BUFFER_SIZE
	    autocommit = False

    for i in range(buffered_messages.qsize()):
        try:
            mySeriesHelper(time=buffered_messages.queue[i]["timestamp"], value=1, host=NODE_ID, node=buffered_messages.queue[i]["nodeID"], geohash=buffered_messages.queue[i]["ghash"], ip=buffered_messages.queue[i]["ip"])
        except:
            print buffered_messages.queue[i]
    print mySeriesHelper._json_body_()
    mySeriesHelper.commit()


# ---------------------------
# Main
# ---------------------------

#buffer the last "received valid message from" messages
buffered_messages = Queue.Queue(MAX_MESSAGES_BUFFER_SIZE)

#get current date
currentDate = '{d.year}-{d.month}-{d.day}'.format(d=datetime.datetime.now())
file = open(LOG_FOLDER_PATH + NODE_ID + "_" + currentDate + ".log","r")
while 1:
    where = file.tell()
    line = file.readline()
    if not line:
        time.sleep(1)
        file.seek(where)
    else:
        if RECEIVED_VALID_MESSAGE in line:
            if not BLACKLIST_STORJ_BRIDGE in line and not BLACKLIST_STORJ_TUNNEL in line:
                message = parseReceivedValidMessageLine(line)

                if message is not "":
                    buffered_messages.put(parseReceivedValidMessageLine(line))

                    if buffered_messages.full():
                        sendToInfluxdb(buffered_messages)
                        buffered_messages.queue.clear()
    testdate = '{d.year}-{d.month}-{d.day}'.format(d=datetime.datetime.now())
    if currentDate != testdate and os.path.exists(LOG_FOLDER_PATH + NODE_ID + "_" + testdate + ".log"):
        currentDate = testdate
        file.close()
        file = open(LOG_FOLDER_PATH + NODE_ID + "_" + currentDate + ".log","r")
