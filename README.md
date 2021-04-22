# VWsFriend
[![Docker COmpose CI](https://github.com/tillsteinbach/VWsFriend/actions/workflows/compose.yml/badge.svg)](https://github.com/tillsteinbach/VWsFriend/actions/workflows/build.yml)

Volkswagen WeConnect© API visualization and control inspired by TeslaMate https://docs.teslamate.org/

## What it looks like
![ID3](./screenshots/id3.png)

## Requirements
* Docker (if you are new to Docker, see [Installing Docker and Docker Compose](https://dev.to/rohansawant/installing-docker-and-docker-compose-on-the-raspberry-pi-in-5-simple-steps-3mgl))
* A Machine that's always on, so VWsFriend can continually fetch data
* External internet access, to talk to the servers

## How to start
* Clone or download the files docker-compose.yml and .env
* To create myconfig.env copy [.env](./.env) file and make changes according to your needs
* Start the stack using your configuration.
```bash
docker-compose --env-file ./myconfig.env up
```
* The first startup can take several minutes because of all the initial settings. Please be patient!
* Open a browser to configure ioBroker (if needed) on http://IP-ADDRESS:8081
* Open a browser to use grafana on http://IP-ADDRESS:3001 with the user and password you selected


## Update
* To update the running VWsFriend configuration to the latest version, run the following commands:
```bash
docker-compose pull
docker-compose --env-file ./myconfig.env up
```

## VWsFriend with Apple Homekit support
![ID3](./screenshots/homekit.jpg)
* Replace the docker-compose command by this to use the homekit override
```bash
docker-compose -f docker-compose-homekit-host.yml
```
This will use host mode for iobroker. This is necessary as the bridge mode will not forward multicast which is necessary for Homekit to work.
If you do not like to share the host network with iobroker you can use macvlan mode:
```bash
docker-compose -f docker-compose-homekit-macvlan.yml
```
Macvlan needs the variables for the IP to choose, the subnetmask and the gateway to be set in your configuration.

## Open improvements
* Deploy datasource and dashboard as grafana app (allows better control)
* More dashboards (also for other cars)
* Change update frequency based on the cars state (more often when car is online)

## Known Issues
* Does not show the nice picture of the car due to unclear license. Need to make a picture on my own when having time

## Credits
* Software used in VWsFriend:
    * [Docker and Docker compose](https://www.docker.com/community/open-source)
    * [ioBroker](https://www.iobroker.net)
    * [ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect)
    * [InfluxDB](https://www.influxdata.com)
    * [Grafana](https://grafana.com)

## Other
We Connect© Volkswagen AG
