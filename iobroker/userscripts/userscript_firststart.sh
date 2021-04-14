#!/bin/bash

echo ' '
echo "Installing dependencies"
echo ' '

iobroker start
iobroker add vw-connect 0
iobroker add javascript 0
iobroker add influxdb 0
iobroker stop

mv /opt/iobroker/iobroker-data/objects.json /opt/iobroker/iobroker-data/objects.json.bak
envsubst < /opt/userscripts/data/influxdb.json > /tmp/influxdb.json
envsubst < /opt/userscripts/data/vwconnect.json > /tmp/vwconnect.json
envsubst < /opt/userscripts/data/javascript.json > /tmp/javascript.json

python3 /opt/userscripts/helpers/mergeJson.py -i /opt/iobroker/iobroker-data/objects.json.bak -o  /opt/iobroker/iobroker-data/objects.json --overwrite /tmp/influxdb.json /tmp/vwconnect.json /tmp/javascript.json

echo '60 second startup to allow ioBroker to recognize the scripts in /opt/javascript'
iobroker start
sleep 30
iobroker state set javascript.0.scriptEnabled.VWsFriendStates true
iobroker state set javascript.0.scriptEnabled.VWsFriendGrafanaAnnotations true
iobroker state set javascript.0.scriptEnabled.VWsFriendStorageConfig true
sleep 30
iobroker logs javascript
iobroker stop
echo 'shutdown again, now manipulating objects.json'

echo 'done, backup can be found in /opt/iobroker/iobroker-data/objects.json.bak'
exit 0
