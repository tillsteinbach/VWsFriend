from enum import Enum, auto
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from vwsfriend.model.trip import Trip
from vwsfriend.util.location_util import locationFromLatLonWithGeofence
from vwsfriend.privacy import Privacy

from weconnect.addressable import AddressableLeaf, AddressableAttribute

LOG = logging.getLogger("VWsFriend")


class TripAgent():
    class Mode(Enum):
        PARKING_POSITION = auto()
        READINESS_STATUS = auto()
        NONE = auto()

    def __init__(self, session, vehicle, updateInterval, privacy):  # noqa: C901
        self.mode = TripAgent.Mode.NONE
        self.session = session
        self.vehicle = vehicle
        self.privacy = privacy
        if Privacy.NO_LOCATIONS in self.privacy:
            LOG.info(f'Privacy option \'no-locations\' is set. Vehicle {self.vehicle.vin} will not record start and destination location')
        self.updateInterval = updateInterval

        self.lastParkingPositionTimestamp = None
        self.lastParkingPositionLatitude = None
        self.lastParkingPositionLongitude = None
        self.trip = session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()

        if self.trip is not None:
            if self.trip.endDate is not None:
                self.lastParkingPositionTimestamp = self.trip.endDate
                if Privacy.NO_LOCATIONS not in self.privacy:
                    self.lastParkingPositionLatitude = self.trip.destination_position_latitude
                    self.lastParkingPositionLongitude = self.trip.destination_position_longitude
            else:
                LOG.info(f'Vehicle {self.vehicle.vin} has still an open trip during startup, closing it now')
            self.trip = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('parking', 'parkingPosition') \
                    and self.vehicle.weConnectVehicle.domains['parking']['parkingPosition'].enabled:
                self.vehicle.weConnectVehicle.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampEnabled,
                                                                                                                     AddressableLeaf.ObserverEvent.ENABLED,
                                                                                                                     onUpdateComplete=True)
                self.vehicle.weConnectVehicle.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__onCarCapturedTimestampChanged,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)
                self.__onCarCapturedTimestampChanged(self.vehicle.weConnectVehicle.domains['parking']['parkingPosition'].carCapturedTimestamp, None)

                if not self.vehicle.weConnectVehicle.domains['parking']['parkingPosition'].error.enabled:
                    LOG.info(f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips based on position')
                    self.mode = TripAgent.Mode.PARKING_POSITION

                    self.vehicle.weConnectVehicle.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampDisabled,
                                                                                                                         AddressableLeaf.ObserverEvent.DISABLED,
                                                                                                                         onUpdateComplete=True)

            if self.mode == TripAgent.Mode.NONE:
                if self.vehicle.weConnectVehicle.statusExists('readiness', 'readinessStatus') \
                        and self.vehicle.weConnectVehicle.domains['readiness']['readinessStatus'].enabled:
                    if self.vehicle.weConnectVehicle.domains['readiness']['readinessStatus'].connectionState is not None \
                            and self.vehicle.weConnectVehicle.domains['readiness']['readinessStatus'].connectionState.enabled:
                        self.vehicle.weConnectVehicle.domains['readiness']['readinessStatus'].connectionState.isActive \
                            .addObserver(self.__onIsActiveChanged, AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True)
                        LOG.info(f'Vehicle {self.vehicle.vin} provides isActive flag in readinessStatus and thus allows to record trips with several minutes'
                                 ' inaccuracy')
                        self.mode = TripAgent.Mode.READINESS_STATUS
                else:
                    self.vehicle.weConnectVehicle.domains.addObserver(self.__onStatusesChange,
                                                                      AddressableLeaf.ObserverEvent.ENABLED,
                                                                      onUpdateComplete=True)

    def __onStatusesChange(self, element, flags):
        if isinstance(element, AddressableAttribute) and element.getGlobalAddress().endswith('parkingPosition/carCapturedTimestamp'):
            # only add if not in list of observers
            if self.__onCarCapturedTimestampEnabled not in element.getObservers(flags=AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True):
                element.addObserver(self.__onCarCapturedTimestampEnabled,
                                    AddressableLeaf.ObserverEvent.ENABLED,
                                    onUpdateComplete=True)
                element.addObserver(self.__onCarCapturedTimestampChanged,
                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                    onUpdateComplete=True)
                element.addObserver(self.__onCarCapturedTimestampDisabled,
                                    AddressableLeaf.ObserverEvent.DISABLED,
                                    onUpdateComplete=True)
                LOG.info(f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips based on position')
                self.mode = TripAgent.Mode.PARKING_POSITION
                self.vehicle.weConnectVehicle.domains.removeObserver(self.__onStatusesChange)
                self.__onCarCapturedTimestampEnabled(element, flags)

    def __onCarCapturedTimestampDisabled(self, element: AddressableAttribute, flags):
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            if element.parent.error.enabled:
                LOG.debug(f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an error set')
                return
            if self.trip is not None:
                LOG.info(f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an open trip, closing it now')
                self.trip = None
            time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(seconds=self.updateInterval)

            if Privacy.NO_LOCATIONS not in self.privacy:
                startPositionLatitude = self.lastParkingPositionLatitude
                startPositionLongitude = self.lastParkingPositionLongitude
            else:
                startPositionLatitude = None
                startPositionLongitude = None
            self.trip = Trip(self.vehicle, time, startPositionLatitude, startPositionLongitude, None, None)
            if Privacy.NO_LOCATIONS not in self.privacy:
                self.trip.start_location = locationFromLatLonWithGeofence(self.session, startPositionLatitude, startPositionLongitude)

            if self.vehicle.weConnectVehicle.statusExists('measurements', 'odometerStatus') \
                    and self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus'].enabled:
                odometerMeasurement = self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus']
                if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                    self.trip.start_mileage_km = odometerMeasurement.odometer.value
            try:
                with self.session.begin_nested():
                    self.session.add(self.trip)
                self.session.commit()
            except IntegrityError as err:
                LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
            LOG.info(f'Vehicle {self.vehicle.vin} started a trip')

    def __onCarCapturedTimestampChanged(self, element, flags):
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            parkingPosition = self.vehicle.weConnectVehicle.domains['parking']['parkingPosition']
            if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                self.lastParkingPositionTimestamp = parkingPosition.carCapturedTimestamp.value
            if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.lastParkingPositionLatitude = parkingPosition.latitude.value
                self.lastParkingPositionLongitude = parkingPosition.longitude.value

    def __onCarCapturedTimestampEnabled(self, element, flags):  # noqa: C901
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            parkingPosition = self.vehicle.weConnectVehicle.domains['parking']['parkingPosition']
            if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                self.lastParkingPositionTimestamp = parkingPosition.carCapturedTimestamp.value
            if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.lastParkingPositionLatitude = parkingPosition.latitude.value
                self.lastParkingPositionLongitude = parkingPosition.longitude.value
            if self.trip is not None:
                if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                    self.trip.endDate = parkingPosition.carCapturedTimestamp.value
                if Privacy.NO_LOCATIONS not in self.privacy:
                    if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                            and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                        self.trip.destination_position_latitude = parkingPosition.latitude.value
                        self.trip.destination_position_longitude = parkingPosition.longitude.value
                        self.trip.destination_location = locationFromLatLonWithGeofence(self.session, parkingPosition.latitude.value,
                                                                                        parkingPosition.longitude.value)

                if self.vehicle.weConnectVehicle.statusExists('measurements', 'odometerStatus') \
                        and self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus'].enabled:
                    odometerMeasurement = self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus']
                    if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                        self.trip.end_mileage_km = odometerMeasurement.odometer.value

                self.trip = None

                LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
            else:
                if flags is not None:
                    LOG.info(f'Vehicle {self.vehicle.vin} provides a parking position, but no trip was started (this is ok during startup)')

    def __onIsActiveChanged(self, element, flags):  # noqa: C901
        if self.mode == TripAgent.Mode.READINESS_STATUS:
            if element.value:
                if self.trip is not None:
                    LOG.info(f'Vehicle {self.vehicle.vin} reports activity but there was an open trip, closing it now')
                    self.trip = None
                time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(seconds=self.updateInterval)
                self.trip = Trip(self.vehicle, time, None, None, None, None)
                if self.vehicle.weConnectVehicle.statusExists('measurements', 'odometerStatus') \
                        and self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus'].enabled:
                    odometerMeasurement = self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus']
                    if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                        self.trip.start_mileage_km = odometerMeasurement.odometer.value
                try:
                    with self.session.begin_nested():
                        self.session.add(self.trip)
                    self.session.commit()
                except IntegrityError as err:
                    LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                LOG.info(f'Vehicle {self.vehicle.vin} started a trip')
            else:
                if self.trip is not None:
                    self.trip.endDate = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
                    if self.vehicle.weConnectVehicle.statusExists('measurements', 'odometerStatus') \
                            and self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus'].enabled:
                        odometerMeasurement = self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus']
                        if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                            self.trip.end_mileage_km = odometerMeasurement.odometer.value

                    self.trip = None

                    LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                else:
                    if flags is not None:
                        LOG.info(f'Vehicle {self.vehicle.vin} reports to be inactive, but no trip was started (this is ok during startup)')

    def commit(self):
        pass
