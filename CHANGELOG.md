# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased] (Available through Edge Tag)

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

[unreleased]: https://github.com/tillsteinbach/VWsFriend/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/tillsteinbach/VWsFriend/releases/tag/v0.1.0
