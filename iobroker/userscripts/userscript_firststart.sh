#!/bin/bash

echo ' '
echo "Installing dependencies"
echo ' '
iobroker add vw-connect 0
iobroker add javascript 0
iobroker add influxdb 0

mv /opt/iobroker/iobroker-data/objects.json /opt/iobroker/iobroker-data/objects.json.bak
envsubst < /opt/userscripts/data/influxdb.json > /tmp/influxdb.json
envsubst < /opt/userscripts/data/vwconnect.json > /tmp/vwconnect.json
python3 /opt/userscripts/helpers/mergeJson.py -i /opt/iobroker/iobroker-data/objects.json.bak -o  /opt/iobroker/iobroker-data/objects.json --overwrite /tmp/influxdb.json /tmp/vwconnect.json

exit 0
