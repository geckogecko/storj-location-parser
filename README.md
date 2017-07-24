# storj-location-parser

Parses the location of nodes that talk with your storj node and sends that information to influxdb 


![grafana_screenshot](https://s18.postimg.org/4qau6w3i1/Selection_003.png)
Download this grafana dashboard from: https://grafana.com/dashboards/2699

## Requirements
```
python -m pip install Geohash
python -m pip install influxdb
```
Geohash: https://github.com/vinsci/geohash
Influxdb python client: https://github.com/influxdata/influxdb-python

## Installation
1. Install Influxdb and Grafana
2. Clone this repo
3. change the configuration of ```storj-location-parser.py```

```
#The nodeID to be monitored
NODE_ID = "23c20fc08ec5c1c23696b46daf0600d1c58170bc"

#INFLUXDB details
INFLUXDB_DATABASE = "renter_monitoring"
INFLUXDB_ADDRESS = "192.168.0.15"
INFLUXDB_PORT = 8086
INFLUXDB_ADMIN = "root"
INFLUXDB_PASSWORD = "root"
```

4. create a database with the name of ```INFLUXDB_DATABASE``` in influxdb with:
```
influx
CREATE DATABASE renter_monitoring
```

5. create the same datasource in grafana
6. import the grafana dashboard from: https://grafana.com/dashboards/2699
7. Run the script with: 
``` python storj-location-parser.py ```
