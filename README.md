# storj-location-parser


![grafana_screenshot](https://www.dropbox.com/s/94y9jdo087rhmel/Selection_003.png?dl=0)

## Requirements
```
python -m pip install Geohash
python -m pip install influxdb
```
Geohash: https://github.com/vinsci/geohash
Influxdb python client: https://github.com/influxdata/influxdb-python

## Configuration
```python
#The nodeID to be monitored
NODE_ID = "23c20fc08ec5c1c23696b46daf0600d1c58170bc"

#INFLUXDB details
INFLUXDB_DATABASE = "renter_monitoring"
INFLUXDB_ADDRESS = "192.168.0.15"
INFLUXDB_PORT = 8086
INFLUXDB_ADMIN = "root"
INFLUXDB_PASSWORD = "root"
```
