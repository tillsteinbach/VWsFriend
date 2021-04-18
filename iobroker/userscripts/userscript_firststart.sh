#!/bin/bash

echo ' '
echo "Installing dependencies"
echo ' '

iobroker start
iobroker add vw-connect 0
iobroker add javascript 0
iobroker add influxdb 0

if [ "$HOMEKIT" = true ] ; then
    iobroker add yahka 0
fi

iobroker set javascript.0 --mirrorPath /opt/javascript
iobroker set javascript.0 --mirrorInstance 0
iobroker set javascript.0 --enableSetObject true
iobroker set javascript.0 --libraries process

iobroker set influxdb.0 --host influxdbbackend
iobroker set influxdb.0 --password $INFLUXDB_ADMIN_PASSWORD
iobroker set influxdb.0 --user $INFLUXDB_ADMIN_USER
iobroker set influxdb.0 --dbname $INFLUXDB_DB

iobroker set vw-connect.0 --interval $VWCONNECT_INTERVAL
iobroker set vw-connect.0 --user $VWCONNECT_USER
iobroker set vw-connect.0 --password $VWCONNECT_PASSWORD
iobroker set vw-connect.0 --pin $VWCONNECT_PIN
iobroker set vw-connect.0 --type $VWCONNECT_TYPE

echo 'wait 10 seconds to allow the adapters to connect'
sleep 10
echo 'starting scripts to set custom states'
iobroker state set javascript.0.scriptEnabled.VWsFriendStates true
echo 'wait 5 seconds to allow the script to execute'
sleep 5
echo 'starting scripts to set grafana annotations'
iobroker state set javascript.0.scriptEnabled.VWsFriendGrafanaAnnotations true
echo 'starting scripts to enable storage'
iobroker state set javascript.0.scriptEnabled.VWsFriendStorageConfig true

if [ "$HOMEKIT" = true ] ; then
echo 'starting scripts to configure homekit'
  iobroker state set javascript.0.scriptEnabled.HomekitConfig true
fi
sleep 5
iobroker logs javascript
iobroker stop
echo 'shutdown again, now everything should be configured and normal startup procedure can be continued'

exit 0
