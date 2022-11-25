# VWsFriend
Volkswagen WeConnect© API visualization and control (HomeKit) inspired by TeslaMate https://docs.teslamate.org/

## What it looks like
<img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/teaser.gif" width="100%">

## Requirements
You need to install python 3 on your system: [How to install python](https://realpython.com/installing-python/). Minimum python version required is 3.8

To make use of all features you have to install and configure several depending projects (grafana, postgresql, ...) most users use the preconfigured docker images at: https://github.com/tillsteinbach/VWsFriend/
If you still want to setup everything on your own, please continue reading.

### Login & Consent
VWsFriend is based on the new WeConnect ID API that was introduced with the new series of ID cars. If you use another car or hybrid you probably need to agree to the terms and conditions of the WeConnect ID interface. Easiest to do so is by installing the WeConnect ID app on your smartphone and login there. If necessary you will be asked to agree to the terms and conditions.

## How to install
If you want to use VWsFriend, the easiest way is to obtain it from [PyPI](https://pypi.org/project/vwsfriend/). Just install using:
```bash
pip3 install vwsfriend
```
### Updates
If you want to update VWsFriend, the easiest way is:
```bash
pip3 install vwsfriend --upgrade
```

## Privacy
Depending on the data provided by your car usage profiles of the cars users can be made (including the locations of trips, refueling and charging). If you need to protect the privacy of the cars users please add ` --privacy no-locations` to the start parameters 

## More information
More information can be found in the Wiki: https://github.com/tillsteinbach/VWsFriend/wiki

## ABPR (A better Route Planner) support
VWsFriend supports sending its data to ABPR out of the box. You just have to generate a user-token in ABRP and configure it for your car in the UI.
Connecting VWsFriend to ABRP enables you to use the current SoC, position, parking and charging state (feature availability depends on your car!) when planning routes in ABRP
If you only want to use the ABPR feature you can try:
```bash
vwsfriend -u user -p password --with-abrp
```
After vwsfriend is started open a browser at http://IP-ADDRESS:4000 and add your user-token in the settings of your car.

## VWsFriend with Apple Homekit support
<img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit.jpg" width="200"><img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit2.jpg" width="200"><img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit3.jpg" width="200"><img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit4.jpg" width="200">

```bash
vwsfriend --with-homekit
```

## VWsFriend with MQTT support (Experimental)
VWsFriend now includes [WeConnect-MQTT](https://github.com/tillsteinbach/WeConnect-mqtt). This enables to use the data from the servers at the same time inside VWsFriend and with MQTT and thus saves additional requests and load on the server.
If you want to know how to configure MQTT, see here: [WeConnect-MQTT Readme](https://github.com/tillsteinbach/WeConnect-mqtt/blob/main/README.md)
VWsFriend is using the same options as WeConnect-MQTT. Just select the options as described in WeConnect-MQTT and add those to VWsFriend when starting.

## Related projects
- [WeConnect-cli](https://github.com/tillsteinbach/WeConnect-cli): A commandline interface to interact with WeConnect
- [WeConnect-MQTT](https://github.com/tillsteinbach/WeConnect-mqtt): A MQTT Client that provides WeConnect data to the MQTT Broker of your choice (e.g. your home automation solution such as [ioBroker](https://www.iobroker.net), [FHEM](https://fhem.de) or [Home Assistant](https://www.home-assistant.io))

## Other
We Connect© Volkswagen AG
