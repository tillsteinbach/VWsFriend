# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased] (Available through Edge Tag)
### Fixed
- Fixed vehicle image loading in Grafana car overview dashboard (thanks to cmantsch)
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

[unreleased]: https://github.com/tillsteinbach/VWsFriend/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.5.0
[0.4.3]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.3
[0.4.2]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.2
[0.4.1]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.1
[0.4.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.4.0
[0.3.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.3.0
[0.2.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.2.0
[0.1.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.1.0
