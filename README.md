# VWsFriend
[![Docker Image CI](https://github.com/tillsteinbach/VWsFriend/actions/workflows/build.yml/badge.svg)](https://github.com/tillsteinbach/VWsFriend/actions/workflows/build.yml)

VW WeConnect visualization and control inspired by TeslaMate https://docs.teslamate.org/

## Requirements
* Docker (if you are new to Docker, see [Installing Docker and Docker Compose](https://dev.to/rohansawant/installing-docker-and-docker-compose-on-the-raspberry-pi-in-5-simple-steps-3mgl))
* A Machine that's always on, so VWsFriend can continually fetch data
* External internet access, to talk to the servers

## How to start
* Clone or download the repository
* Change the configuration in [config.env](./config.env)
* Start the stack using the configuration
```bash
docker-compose --env-file ./config up
```
* Open a browser to configure ioBroker on http://IP-ADDRESS:8081
* Open a browser to configure grafana on http://IP-ADDRESS:3001 with the user and password you selected
