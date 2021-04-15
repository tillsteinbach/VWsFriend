# VWsFriend
[![Docker Image CI](https://github.com/tillsteinbach/VWsFriend/actions/workflows/build.yml/badge.svg)](https://github.com/tillsteinbach/VWsFriend/actions/workflows/build.yml)

Volkswagen WeConnect© API visualization and control inspired by TeslaMate https://docs.teslamate.org/

## What it looks like
![ID3](./screenshots/id3.png)

## Requirements
* Docker (if you are new to Docker, see [Installing Docker and Docker Compose](https://dev.to/rohansawant/installing-docker-and-docker-compose-on-the-raspberry-pi-in-5-simple-steps-3mgl))
* A Machine that's always on, so VWsFriend can continually fetch data
* External internet access, to talk to the servers

## How to start
* Clone or download the repository
* Change the configuration in [config.env](./config.env)
* Start the stack using your configuration. To create myconfig.env copy .env file
```bash
docker-compose --env-file ./myconfig.env up
```
* The first startup can take several minutes because of all the initial settings. Please be patient!
* Open a browser to configure ioBroker on http://IP-ADDRESS:8081
* Open a browser to configure grafana on http://IP-ADDRESS:3001 with the user and password you selected

## Open improvements
* Deploy datasource and dashboard as grafana app (allows better control)
* More dashboards (also for other cars)
* Also add Homekit configuration to ioBroker

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
