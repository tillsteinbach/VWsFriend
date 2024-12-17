# VWsFriend
[![GitHub sourcecode](https://img.shields.io/badge/Source-GitHub-green)](https://github.com/tillsteinbach/VWsFriend/)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/tillsteinbach/VWsFriend)](https://github.com/tillsteinbach/VWsFriend/releases/latest)
[![GitHub](https://img.shields.io/github/license/tillsteinbach/VWsFriend)](https://github.com/tillsteinbach/VWsFriend/blob/master/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/tillsteinbach/VWsFriend)](https://github.com/tillsteinbach/VWsFriend/issues)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vwsfriend?label=PyPI%20Downloads)](https://pypi.org/project/vwsfriend/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vwsfriend)](https://pypi.org/project/vwsfriend/)
[![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/tillsteinbach/vwsfriend?sort=semver)](https://hub.docker.com/r/tillsteinbach/vwsfriend)
[![Docker Pulls](https://img.shields.io/docker/pulls/tillsteinbach/vwsfriend)](https://hub.docker.com/r/tillsteinbach/vwsfriend)
[![Donate at PayPal](https://img.shields.io/badge/Donate-PayPal-2997d8)](https://www.paypal.com/donate?hosted_button_id=2BVFF5GJ9SXAJ)
[![Sponsor at Github](https://img.shields.io/badge/Sponsor-GitHub-28a745)](https://github.com/sponsors/tillsteinbach)

[![Docker Compose CI](https://github.com/tillsteinbach/VWsFriend/actions/workflows/compose.yml/badge.svg)](https://github.com/tillsteinbach/VWsFriend/actions/workflows/build.yml)

Volkswagen WeConnect© API visualization and control (HomeKit) inspired by TeslaMate https://docs.teslamate.org/

## What it looks like
<img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/teaser.gif" width="100%">

## Requirements
* Docker 20.10.10 or later (if you are new to Docker, see [Installing Docker and Docker Compose](https://docs.docker.com/engine/install/) or for [Raspberry Pi](https://dev.to/rohansawant/installing-docker-and-docker-compose-on-the-raspberry-pi-in-5-simple-steps-3mgl)), docker-compose needs to be at least version 1.27.0 (you can check with `docker compose --version`)
* A Machine that's always on, so VWsFriend can continually fetch data
* External internet access, to talk to the servers

## Login & Consent
VWsFriend is based on the new WeConnect API that was introduced with the new series of ID cars. If you use another car or hybrid you probably need to agree to the terms and conditions of the new WeConnect interface. Easiest to do so is by installing the Volkswagen app on your smartphone and login there. If necessary you will be asked to agree to the terms and conditions.

## How to start
* Clone or download the files [docker-compose.yml](https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/docker-compose.yml) and [.env](https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/.env)
* To create myconfig.env copy [.env](https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/.env) file and make changes according to your needs
* Start the stack using your configuration.
```bash
docker compose --env-file ./myconfig.env up
```

* Open a browser to use the webinterface on http://IP-ADDRESS:4000
* Open a browser to use grafana on http://IP-ADDRESS:3000 with the user and password you selected

## More information
More information can be found in the Wiki: https://github.com/tillsteinbach/VWsFriend/wiki

## Update
* To update the running VWsFriend configuration to the latest version, run the following commands:
```bash
docker compose pull
docker compose --env-file ./myconfig.env up
```

## Privacy
Depending on the data provided by your car usage profiles of the cars users can be made (including the locations of trips, refueling and charging). If you need to protect the privacy of the cars users please add ` --privacy no-locations` to the `ADDITIONAL_PARAMETERS` in your myconfig.env file

## ABPR (A better Route Planner) support
VWsFriend supports sending its data to ABPR out of the box. You just have to generate a user-token in ABRP and configure it for your car in the UI.
Connecting VWsFriend to ABRP enables you to use the current SoC, position, parking and charging state (feature availability depends on your car!) when planning routes in ABRP

## VWsFriend with Apple Homekit support
<img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit.jpg" width="200"><img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit2.jpg" width="200"><img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit3.jpg" width="200"><img src="https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/screenshots/homekit4.jpg" width="200">

* Replace the docker-compose file by [docker-compose-homekit-host.yml](https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/docker-compose-homekit-host.yml) to use the homekit override
```bash
docker compose -f docker-compose-homekit-host.yml --env-file ./myconfig.env up
```
This will use host mode for vwsfriend. This is necessary as the bridge mode will not forward multicast which is necessary for Homekit to work.
Host mode is not working on macOS. The reson is that the network is still virtualized. See also [Known Issues](#known-issues).

If you do not like to share the host network with vwsfriend you can use macvlan mode [docker-compose-homekit-macvlan.yml](https://raw.githubusercontent.com/tillsteinbach/VWsFriend/main/docker-compose-homekit-macvlan.yml):
```bash
docker compose -f docker-compose-homekit-macvlan.yml --env-file ./myconfig.env up
```
In macvlan mode VWsFriend will appear as a seperate computer in the network thus you also have to set HOMEKIT_IP to a free IP address in your network in the .env-file.
HOMEKIT_MASK and HOMEKIT_GW need to be configured with the correct netmask and gateway settings for your network. 

In macvlan mode you reach VWsFriends UI on the configured IP at port 4000

Macvlan mode is not supported on macOS! See also [Known Issues](#known-issues).

## VWsFriend with MQTT support
VWsFriend also includes [WeConnect-MQTT](https://github.com/tillsteinbach/WeConnect-mqtt). This enables to use the data from the servers at the same time inside VWsFriend and with MQTT and thus saves additional requests and load on the server.
If you want to know how to configure MQTT, see here: [WeConnect-MQTT Readme](https://github.com/tillsteinbach/WeConnect-mqtt/blob/main/README.md)
VWsFriend is using the same options as WeConnect-MQTT. Just select the options as described in WeConnect-MQTT and add those to the `ADDITIONAL_PARAMETERS`.

## Automated Updates
As there are continuously updates to the WeConnect API VWsFriend my stop unexpectedly working. I try to push updates in this case as fast as possible. You can configure to get these updates automatically by adding watchtower to your docker-compose.yml file:
```bash
watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 3600 --cleanup
```
If you want to be sure that the update only happens at a certain time of the day to prevent updating in times where you use the car you can also schedule update times like this:
```bash
    command: --schedule "0 0 2 * * *" --cleanup
```
The example shifts the update time to 2:00 (UTC)

## Automated Backups
For automated backups I recommend using [docker-volume-backup](https://github.com/offen/docker-volume-backup). You just need to add an additional service to your docker-compose.yml to allow it to make regular backups.
This example shows a configuration for daily backups on a webdav enabled NAS:
```bash
backup:
  image: offen/docker-volume-backup:latest
  restart: always
  environment:
    WEBDAV_URL: https://mynas:5006
    WEBDAV_URL_INSECURE: 'true'
    WEBDAV_PATH: /home/backup/VWsFriend
    WEBDAV_USERNAME: backupuser
    WEBDAV_PASSWORD: secretbackuppassword
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - postgresdb_data:/backup/postgresdb-backup:ro
    - grafana_data:/backup/grafana-backup:ro
    - vwsfriend_data:/backup/vwsfriend-backup:ro
```
docker-volume-backup supports various [backup locactions](https://offen.github.io/docker-volume-backup/recipes/) and can also enable [different retention policies](https://offen.github.io/docker-volume-backup/how-tos/define-different-retention-schedules.html).

## Known Issues
* On Raspberry Pi the library libseccomp2 needs to be at least 2.4.4. Most current images for the Raspberry Pi still ship an outdated version. You can update it like that:
```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 04EE7237B7D453EC 648ACFD622F3D138
echo "deb http://deb.debian.org/debian buster-backports main" | sudo tee -a /etc/apt/sources.list.d/buster-backports.list
sudo apt update
sudo apt install -t buster-backports libseccomp2
```
* Ironically you cannot host VWsFriend with Homekit support on a macOS machine. The reason is that there is no way to get the advertisements via multicast out of the container into the network. If you want to use the Homekit feature you have to host VWsFriend on a Linux machine. If someone is able to make a setup work on macOS, please let me know to allow me to update the documentation!

## Open improvements
* Deploy datasource and dashboard as grafana app (allows better control)
* Change update frequency based on the cars state (more often when car is online)

## Credits
* Software used in VWsFriend:
    * [Docker and Docker compose](https://www.docker.com/community/open-source)
    * [PostgreSQL](https://www.postgresql.org)
    * [Grafana](https://grafana.com)
    * [HAP-python](https://github.com/ikalchev/HAP-python)
    * And several more

## Related projects
- [WeConnect-cli](https://github.com/tillsteinbach/WeConnect-cli): A commandline interface to interact with WeConnect
- [WeConnect-MQTT](https://github.com/tillsteinbach/WeConnect-mqtt): A MQTT Client that provides WeConnect data to the MQTT Broker of your choice (e.g. your home automation solution such as [ioBroker](https://www.iobroker.net), [FHEM](https://fhem.de) or [Home Assistant](https://www.home-assistant.io))
- [IDDataLogger](https://github.com/robske110/IDDataLogger)(not maintaned by me): A data logger for Volkswagen ID vehicles written in PHP

## Seat, Cupra, Skoda IV, ...
Now owning a Skoda vehicle I'm about to make a rewrite of this library called [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity), I hope this will be ready for a first release in early 2025

## Other
We Connect© Volkswagen AG
