# ioBroker provisioned for VWsFriend Software
This image provisions ioBroker with the following Adapters:
- vw-connect
- influxdb
- javascript
- yahka (optional)

It also configures all adapters based on the environment variables and provides and enables the following scripts:
- VWsFriendStates.js: Calculates additional parameters based on user defined values
- VWsFriendStorageConfig.js: Configures iobroker to store necessary measurements in influxdb iobroker database
- VWsFriendGrafanaAnnotations.js: Provides Annotations to Grafana in influxdb iobroker database
- HomkitConfig.js: Configures Homekit according to the cars connected
