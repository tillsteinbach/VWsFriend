# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased] (Available through [edge](https://hub.docker.com/r/tillsteinbach/vwsfriend/tags?page=1&name=edge) tag)
- No unreleased changes so far

## [0.24.9] - 2025-11-29
### Fixed
- Fixes refresh token handling that was broken in 0.24.8 due to typo when backporting changes

## [0.24.8] - 2024-11-29
### Fixed
- Fixes login due to changes in the login form

## [0.24.7] - 2024-09-14
### Fixed
- fix bug in database migration

## [0.24.6] - 2024-09-13
### Fixed
- fix bug that lead to a crash with Unkown warning lights

### Added
- Adds several new attributes and status

### Changed
- Updated API to 0.60.5
- Various dependencies updated

## [0.24.5] - 2024-08-02
### Added
- Added several attributes

### Changed
- Updated API to 0.60.4
- Updated Grafana to 11.1.3
- Various dependencies updated

## [0.24.4] - 2024-03-03
### Fixed
- Fixed a bug with the ABRP agent after adding battery temperature

## [0.24.3] - 2024-03-03
### Fixed
- Improved behaviour where new charging sessions were created when car was conservating
- Trips are now recorded with position even when there was no position available on VWsFriend startup

### Added
- Charts for battery temperature (for selected cars only)
- Send battery temperature to ABRP (for selected cars only)


### Changed
- Updated API to 0.60.2
- Updated Grafana to 10.1.2
- Various dependencies updated

## [0.24.2] - 2023-11-28 
### Fixed
- Bug with Homekit Battery Temperature Sensor

## [0.24.1] - 2023-11-28 
### Fixed
- Bug with Homekit Battery Temperature Sensor
- Allow Meter values in UI with more than 1000kWh

## [0.24.0] - 2023-11-25 
### Added
- Support for python 3.12 added
- Support for battery temperature on supported vehicles (will be logged to the database - and shown in the future, also new Temperature Sensor in Apple Home)
- Flashing of Indicator lights now possible via Apple Home (displayed as a Light Switch)

### Fixed
- Trip agent will now record trips later when during startup no parking position was available

### Changed
- Updated API to 0.59.5
- Updated Grafana to 10.1.2
- Various dependencies updated
- Improved behaviour when 429 errors (too many requests) are reported

## [0.23.11] - 2023-07-14 
### Fixed
- Fixes problem where VWsFriend was unresponsive
- Fixes crash when ABRP answers with empty message

### Added
- MQTT: Adding trip statistics for supported cars

### Changed
- Car goes offline after 15min of no data now
- Updated API to 0.56.2
- Upgrade Grafana to 10.0.1

## [0.23.10] - 2023-04-28 
### Fixed
- Fixes problem with stability

### Changed
- Updated API to 0.55.0
- Upgrade Grafana to 9.5.1

## [0.23.9] - 2023-03-04 
### Fixed
- Fixes problem with Tags by downgrading grafana

### Changed
- Downgrade Grafana to 9.3.2

## [0.23.8] - 2023-03-02 
### Fixed
- Fixes unknown operation error

### Added
- Add database index for several classes to improve query performance

### Changed
- Updated API to 0.54.2
- Updated Grafana to 9.4.2

## [0.23.7] - 2023-02-28
### fixed
- Changed URLs to the new URLs necessary to contact the backend

### Changed
- Updated API to 0.54.1

## [0.23.6] - 2023-02-22
### fixed
- Fixed Timezone bug in settings form

## [0.23.5] - 2023-02-22
### fixed
- Small bugfix release

## [0.23.4] - 2023-02-21
### fixed
- Fix making MQTT more stable
- Problem with missing token
- Add new error state (Thanks to user madd0)
- Add new timer attribute targetSOC_pct
- Fixed bug that could make attributes disappear on certain values

### Added
- Add ENGINE category for warning lights

### Changed
- Updated API to 0.54.0

## [0.23.3] - 2023-02-11
### fixed
- Error when trying to change vehicle settings

## [0.23.2] - 2023-02-03
### Changed
- Updated API to 0.51.1
- Updated various dependencies

## [0.23.1] - 2022-11-30
### Fixed
- Fixed bug where trips were not recorded anymore for cars with firmware <u
### Changed
- Updated API to 0.50.1

## [0.23.0] - 2022-11-25
### Added
- Support for python 3.11
- Add new currentFuelLevel_pct attribut
- Add invalid door lock state
- Tire warning light category

### Fixed
- Bug with times on self hosted postgres databases that do not have UTC as a default timezone
- Bug where database was not updated after restart of the container
- Bug on status page when timestamp was not set
- Bug where updates became stuck after a temporary authentification error

### Changed
- Default python version used now is 3.11
- Relogin if the refresh token expired
- Don't store cookies in between requests
- No cache header added
- First failed contact with vw servers will trigger warning not error
- Updated API to 0.50.0
- Updated MQTT-API to 0.41.0
- Updated Grafana to 9.2.6

### Removed
- Support for python 3.7


## [0.22.3] - 2022-10-18
### Fixed
- Bug on settings page fixed

## [0.22.2] - 2022-10-17
### Fixed
- Bug with warning lights for tire pressure
- Bug for charging stations that don't have an operator

### Changed
- Updated API to 0.48.3
- Updated MQTT-API to 0.40.3
- Updated Grafana to 9.2.0
- Removed Plotly plugin and use native grafana XY plot now

## [0.22.1] - 2022-10-04
### Added
- Add invalid door lock state
- Graph and routes on map now sync with each other

### Fixed
- Bug with honk and flash endpoint
- Bug where VWsFriend crashed when no location could be retrieved
- Bug when no data could be retrieved on startup

### Changed
- Updated API to 0.48.2
- Updated Grafana to 9.1.7
- Removed Plotly plugin and use native grafana XY plot now

## [0.22.0] - 2022-09-23
### Added
- Allow to hide and sort vehicles in the grafana select box through vehicle settings
- Tire warning light category

### Fixed
- Bug with honk and flash endpoint

### Changed
- Updated API to 0.48.1
- Updated Grafana to 9.1.6

## [0.21.0] - 2022-08-19
### Added
- Support for S-PIN
- Locking support in HomeKit (only selected cars), experimental!

### Changed
- Replaced trackmaps plugin with geomaps plugin for all track dashboards
- Charging statistics with smaller binning below 15kW
- Updated API to 0.47.0
- Updated Grafana to 9.1.0


## [0.20.1] - 2022-08-02 (Celebrating 100 stars on GitHub!)
### Added
- Attributes for diesel cars
- New status departureTimersStatus & chargingProfilesStatus

### Changed
- Status images in Grafana are now served by Grafana itself.
- Some small changes to the Dashboards
- Updated API to 0.45.1
- Updated Grafana to 9.0.6

## [0.20.0] - 2022-07-25
### Added
- Weconnect-mqtt is now included in VWsFriend
- New icons on maps

### Fixed
- Trip recording fixed
- Make start date optional in charging session edit form

### Changed
- Updated API to 0.45.1
- Updated Grafana to 9.0.4
- Ubuntu updated from 21.10 to 22.04
- Python from 3.9 to 3.10
- ADDITIONAL_PARAMETERS can now be chaged from .env file
- Line interpolation changed to step for a lot of plots
- Tooltip-Mode changed from single to all

### Thank you!
Special thanks to user @thgau for sponsoring this release!

## [0.19.2] - 2022-06-28
### Added
- Added ChargingState: DISCHARGING and ChargeMode: HOME_STORAGE_CHARGING, IMMEDIATE_DISCHARGING
- Added plug led and externalPower state to live dashbaord

### Fixed
- Fix (again) continuation of charging session with auto unlock
- Removed unnecessary save dialog in grafana
- Fixed error with warning light icon

### Changed
- Maps are using build in dashboard panels again
- Updated API to 0.44.2
- Updated Grafana to 9.0.1

## [0.19.1] - 2022-06-23
### Added
- Added new values for attribute externalPower: unsupported, active
- Added new values for attribute chargingStatus: unsupported
- Added new values for attribute ledColor: green, red

### Changed
- More states are now used in Homekit
- Updated API to 0.43.2

## [0.19.0] - 2022-06-22 (Happy birthday Peer!)
### Added
- Added new attributes: brandCode, autoUnlockPlugWhenChargedAC, ledColor, externalPower
- Added number of battery cycles to charging statistics

### Fixed
- Fix ordering of entrys in database UI
- Add NOT_READY_FOR_CHARGING to states that end a charging session
- Fix continuation of charging session with auto unlock

### Changed
- Updated API to 0.43.0
- Updated Grafana to 9.0.0

## [0.18.2] - 2022-06-13
### Added
- port and address of homekit server can be set through commandline

### Changed
- Default interval decreased from 300 to 180 seconds

### Fixed
- UI accepts times with :00 seconds

## [0.18.1] - 2022-06-12
### Changed
- Unlocking does not end a charging session anymore (necessary for PV excess charging)
- More charging states used in the state machine (Should make recordng of charging sessions more stable).
- Use step interpolation (not linear) in charging session details for the charging power.

## [0.18.0] - 2022-06-09
### Added
- Maintenance dashboard added
- VWsFriend version in grafana visible
- The timezone in which the vehicle is operated can be set
- Added new panel for the duration by time of day for reoccuring trips
- In charging details the state (charging, readyForCharging, ...) are displayed

### Fixed
- Refueling statistics are now correct when the real value was not added
- Efficiency was not correctly shown for hybrid cars in some situations
- Interrupts of a charging session (e.g. due to PV excess charging) will not create a new session. Only disconnecting or unlocking the plug does.

### Changed
- The charging speed by SoC is only shown from DC charging
- Live view now also shows the target SoC when charging
- Updated API to 0.41.0
- Updated Grafana to 8.5.5

## [0.17.0] - 2022-05-12
### Added
- New live dashboard (still experimental!)
- Maintenance and Warning light occurances are now recorded and displayed in dashboard if supported by the car
- New aggregated trip dashboard showing statistics for reoccuring trips

### Fixed
- Improvements in dashboards
- More robust against concurrent database manipulation in the UI

### Changed
- Updated API to 0.40.0
- Updated Grafana to 8.5.2

## [0.16.6] - 2022-04-04

### Fixed
- Make login error messages more clear
- Retry if login fails

### Added
- Climatisation state invalid
- Make UI host and port configurable

### Changed
- Improved error messages on login errors
- Updated API to 0.38.1
- Updated Grafana to 8.4.5

## [0.16.5] - 2022-03-14
### Fixed
- Fixed live datasource credentials
- Removed warning for enums when starting up

### Changed
- Improved trip detection (not creating trips when plugged to charger)

### Added
- Added caching to json status

## [0.16.4] - 2022-03-06
### Fixed
- Remove warning if primary total capacity is empty (necessary for hybrid vehicles!)

## [0.16.3] - 2022-03-06
### Fixed
- Fixed vehicle settings form for hybrid vehicles

## [0.16.2] - 2022-03-06
### Fixed
- Fixed times in logging that were still wrong for some users.

## [0.16.1] - 2022-03-04
### Fixed
- Catch error when server is not responding correctly during login
- Correct calculation of start/end/duration in states panel on overview dashboard
- Correctly handle all charging states in homekit
- Use grafana dashboard timezone in "recent events log"

### Changed
- Updated API to 0.37.2
- Updated Grafana to 8.4.3

## [0.16.0] - 2022-02-25
### Added
- New feature to tag entries and filter based on those tags
- Possibility to manipulate database through UI
- Use AC/DC charging information from car

### Changed
- Various improvements in grafana dashboards
- Updated API to 0.37.0
- Updated Grafana to 8.4.1

## [0.15.1] - 2022-02-12
### Fixed
- Fixes bug in charging state API fixing procedure

### Changed
- Updated API to 0.36.4

## [0.15.0] - 2022-02-11
***Warning this update requires you to update your docker-compse.yml and env file!***
### Fixed
- Fixes login issue due to changes in the login form

### Added
- Passwort protection for UI
- Geofences allow to specify areas that are always resolved to a specific location and/or charger
- Chargers that are not known can be added
- /json endpoint to receive data in json format
- Added status fail_charge_plug_not_connected

### Changed
- VWsFriend will now more reliably find a gas station when the car is being refueled.
- Refactors the OAuth procedure
- More agressively ask for changing the default password
- Updated API to 0.36.3
- Updated several dependencies
- Updated Grafana to 8.3.6

## [0.14.2] - 2022-02-04
### Fixed
- Update of 0.14.1 fix that fails on some instances

## [0.14.1] - 2022-02-04
### Fixed
- Add missing CONSERVATION Enum to database schema

## [0.14.0] - 2022-01-28
### Fixed
- Login to WeConnect works again after changes on login page
- Homekit does not forget notification and favorit setting anymore

### Added
- Logging can now send mails if an error occurs

### Changed
- Updated API to 0.35.1

## [0.13.1] - 2022-01-24
### Fixed
- Small bugfix in request tracking that will reduce the load of the server running VWsFriend

### Changed
- Updated API to 0.35.0

## [0.13.0] - 2022-01-23
### Changed
- Homekit gives now much faster feedback when controling the car (Even faster than WeConnect App)
- Minor improvements to grafana dashboards
- Updated API to 0.34.0

### Added
- new parameter --hide-repeated-log that suppresses repeating messages from logging (does not apply to errors)
- new parameter --privacy allowing to disable location tracking

### Fixed
- More robust against server errors
- Hides status 204 on missing parking position
- Charging power is recorded with decimals
- Fix division by zero in grafana dashboards

## [0.12.0] - 2021-12-15
### Added
- Recording of trips for ID vehicles

### Changed
- Interval can be decresed to 180 seconds
- Technical fields are now hidden in the tables
- Removed interpolation from charging graph

## [0.11.0] - 2021-12-11
### Added
- Added cartype gasoline
- Added UnlockPlugState permanent

### Changed
- Updated API to 0.27.0
- Updated Grafana to 8.3.1


## [0.10.1] - 2021-12-03
### Fixed
- Adding missing Enum types to database

## [0.10.0] - 2021-12-01
### Added
- ABRP now receives the new est_battery_range parameter
- Enabled grafana livenow mode
- New attributes in status page

### Fixed
- Ordering of refueling sessions
- Also use parking position from the past 15 mins when refueling
- Grouping by operator if there are several entries for a operator
- Deal with missing vehicle images

### Changed
- Updated Grafana to 8.2.5
- Updated requirements for forms
- Updated API to 0.25.1
- Changed all graphs from old version to the new time-series variant

## [0.9.6] - 2021-11-01
### Fixed
- Fixed an error occuring when the server unexpectedly closes the connection

### Changed
- Updated API to 0.22.1

## [0.9.5] - 2021-11-01
### Fixed
- Changed Ubuntu Image from 21.04 to 21.10 for better Raspberry Pi support

### Changed
- Updated API to 0.22.0

## [0.9.4] - 2021-10-27
### Added
- Possibility to configure database host, port and databasename

### Fixed
- Ghost trips when Server reports error

## [0.9.3] - 2021-10-22
### Fixed
- Create provisioning folder if not existing

## [0.9.2] - 2021-10-22
### Fixed
- Corrected filename when restoring

## [0.9.1] - 2021-10-21
### Fixed
- Correct postgres version to 13 in dockerfile

### Changed
- Updated API to 0.21.5

## [0.9.0] - 2021-10-20
### Added
- Possibility to backup and restore the database

## [0.8.2] - 2021-10-19
### Fixed
- Refueling seperated in two parts is now joined into one session

## [0.8.1] - 2021-10-16
### Fixed
- installation of panomap plugin

## [0.8.0] - 2021-10-14
### Added
- Charging map in charging statistics

### Fixed
- Caching of pictures improved
- Bug in Homekit Dummy device when no name was configured

### Changed
- More slim grafana configuration, don't distracting with unused features
- Updated API to 0.21.3

## [0.7.0] - 2021-10-12
### Fixed
- Interval is executed more precisely
- Will deal with corrupted cache file by deleting cache
- Various improvements in dashboards (e.g. optimized queries)
- Corrupted graphs for consumption, range and efficiency
- Unwanted refuel session entries when the car suddenly finds one or two percent of fuel

### Added
- New dashboard for journeys added
- It is now possible to add real amount and cost for refueling of gasoline cars and hybrids
- Statistics for the responsetime are collected

### Changed
- Updated API to 0.21.1
- Getting mileage from new odometerMeasurement instead of maintenanceStatus field
- Updated requirements for alembic to 1.7.4 and hyp-python to 4.3.0

## [0.6.0] - 2021-10-06
### Fixed
- Fixed recording of trips
- Fixed lost room assignment in HomeKit setup
- Problems with HomeKit setting climatization correctly
- Small improvements on Grafana Dashboards
- Fixed 32Bit ARM docker image building

### Changed
- Updated API to 0.21.0

### Added
- collecting errors in database for future visualization
- Possibility to correct recorded data and add missing information
- Status page car images now displays badges indicating lock/charging/etc
- Possiblity to configure logging output format
- Added time in logging

## [0.5.4] - 2021-09-23
### Fixed
- Fix due to changes in the API

### Changed
- Updated API to 0.20.12

## [0.5.3] - 2021-09-16
### Fixed
- Typo in default value in Dockerfile

## [0.5.2] - 2021-09-16
### Added
- Use retry mechanism for all http requests

### Changed
- Various improvements in the Dashboards. Better compatibility with legacy cars

## [0.5.1] - 2021-09-13
### Fixed
- Fixed vehicle image loading in Grafana car overview dashboard (thanks to [cmantsch](https://github.com/cmantsch))
- Database migration process
- VWsFriend is now waiting for the database to be available

## [0.5.0] - 2021-09-10
### Added
- New statistics dashboard for daily, weekly, monthly, yearly overview
- New statistics dashboard for mileage (including projection)

### Fixed
- Problem with recording fueling on hybird and fossil cars 

## [0.4.3] - 2021-09-09
### Fixed
- Crash when experiencing connection problems, e.g. due to internet outage
- Version footer
- Catching up a running charging session after restart

## [0.4.2] - 2021-09-08
### Fixed
- Some problems in grafana dashboards
- Problems with commiting changes to the database
- Several fixes in Grafana

### Added
- Possibility to make changes to trips
- Possibility to see version information in UI

## [0.4.1] - 2021-09-07
Happy Birthday Pia!

### Fixed
- Problem on database commit

### Changed
- Updated API to 0.20.6

## [0.4.0] - 2021-08-25
### Added
- New Homekit Accessories (Plug and Lock) added
- Homekit can now control charging and climatization (temperature and on/off state)
- Homekit configuration through UI

### Fixed
- Trips work again after changes to WeConnect Service

## [0.3.0] - 2021-08-24
This is a complete rewrite of VWsFriend using a self developed API. It drops ioBroker

### Added
- Several new dashboards for refueling (hybrid and gasoline only), charging sessions, trips (only when parking position is provided), ...
- Added support to forward telemetry to ABPR (A better route planner)
- Web Userinterface to see status and configure settings
- a lot more...

### Changed
- Now uses PostgreSQL instead of Influx

### Removed
- ioBroker is not shipped anymore with VWsFriend. If you still want to use ioBroker, you can use ioBroker with [WeConnect-mqt](https://github.com/tillsteinbach/WeConnect-mqtt).

## [0.2.0] - 2021-04-25
### Added
- Now understanding climate state 'ventilation' in grafana and homekit
- carCapturedTimestampLatest in userdata area

### Changed
- Updating Grafana from 7.5.3 to 7.5.4
- More accurate Grafana Annotations by using timestamp from server
- Last connection information on dashboard now based on latest timestamp from API
- All states written by VWsFriend to iobroker are now set with ack: true

### Fixed
- Text is now consistently in english

## [0.1.0] - 2021-04-22
Initial release to enable "latest" tag on dockerhub

[unreleased]: https://github.com/tillsteinbach/VWsFriend/compare/v0.24.9...HEAD
[0.24.9]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.9
[0.24.8]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.8
[0.24.7]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.7
[0.24.6]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.6
[0.24.5]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.5
[0.24.4]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.4
[0.24.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.3
[0.24.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.2
[0.24.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.1
[0.24.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.24.0
[0.23.11]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.11
[0.23.10]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.10
[0.23.9]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.9
[0.23.8]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.8
[0.23.7]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.7
[0.23.6]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.6
[0.23.5]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.5
[0.23.4]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.4
[0.23.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.3
[0.23.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.2
[0.23.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.1
[0.23.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.23.0
[0.22.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.22.3
[0.22.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.22.2
[0.22.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.22.1
[0.22.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.22.0
[0.21.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.21.0
[0.20.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.20.1
[0.20.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.100
[0.19.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.19.2
[0.19.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.19.1
[0.19.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.19.0
[0.18.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.18.2
[0.18.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.18.1
[0.18.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.18.0
[0.17.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.17.0
[0.16.6]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.6
[0.16.5]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.5
[0.16.4]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.4
[0.16.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.3
[0.16.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.2
[0.16.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.1
[0.16.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.16.0
[0.15.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.15.1
[0.15.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.15.0
[0.14.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.14.2
[0.14.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.14.1
[0.14.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.14.0
[0.13.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.13.1
[0.13.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.13.0
[0.12.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.12.0
[0.11.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.11.0
[0.10.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.10.1
[0.10.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.10.0
[0.9.6]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.6
[0.9.5]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.5
[0.9.4]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.4
[0.9.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.3
[0.9.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.2
[0.9.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.1
[0.9.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.9.0
[0.8.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.8.2
[0.8.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.8.1
[0.8.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.8.0
[0.7.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.7.1
[0.7.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.7.0
[0.6.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.6.0
[0.5.4]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.5.4
[0.5.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.5.3
[0.5.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.5.2
[0.5.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.5.1
[0.5.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.5.0
[0.4.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.3
[0.4.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.2
[0.4.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.1
[0.4.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.0
[0.3.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.3.0
[0.2.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.2.0
[0.1.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.1.0
