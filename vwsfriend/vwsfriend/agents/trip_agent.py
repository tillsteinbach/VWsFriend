import logging
from datetime import datetime, timezone

from sqlalchemy import and_

from vwsfriend.model.trip import Trip
from vwsfriend.util.location_util import locationFromLatLon

from weconnect.addressable import AddressableLeaf, AddressableAttribute

LOG = logging.getLogger("VWsFriend")


class TripAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle

        self.trip = session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()
        if self.trip is not None:
            if self.trip.endDate is not None:
                self.lastParkingPositionTimestamp = self.trip.endDate
                self.lastParkingPositionLatitude = self.trip.destination_position_latitude
                self.lastParkingPositionLongitude = self.trip.destination_position_longitude
            else:
                LOG.info(f'Vehicle {self.vehicle.vin} has still an open trip during startup, closing it now')
            self.trip = None
        else:
            self.lastParkingPositionTimestamp = None
            self.lastParkingPositionLatitude = None
            self.lastParkingPositionLongitude = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'parkingPosition' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['parkingPosition'].enabled:
                self.vehicle.weConnectVehicle.statuses['parkingPosition'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                           AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                           onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(self.vehicle.weConnectVehicle.statuses['parkingPosition'].carCapturedTimestamp, None)
                self.vehicle.weConnectVehicle.statuses['parkingPosition'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampDisabled,
                                                                                                           AddressableLeaf.ObserverEvent.DISABLED,
                                                                                                           onUpdateComplete=True)
                LOG.info(f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips')
            else:
                self.vehicle.weConnectVehicle.statuses.addObserver(self.__onStatusesChange,
                                                                   AddressableLeaf.ObserverEvent.ENABLED,
                                                                   onUpdateComplete=True)

    def __onStatusesChange(self, element, flags):
        if isinstance(element, AddressableAttribute) and element.getGlobalAddress().endswith('parkingPosition/carCapturedTimestamp'):
            # only add if not in list of observers
            if self.__onCarCapturedTimestampChange not in element.getObservers(flags=AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True):
                element.addObserver(self.__onCarCapturedTimestampChange,
                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                    onUpdateComplete=True)
                element.addObserver(self.__onCarCapturedTimestampDisabled,
                                    AddressableLeaf.ObserverEvent.DISABLED,
                                    onUpdateComplete=True)
                LOG.info(f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips')
                self.vehicle.weConnectVehicle.statuses.removeObserver(self.__onStatusesChange)
                self.__onCarCapturedTimestampChange(element, flags)

    def __onCarCapturedTimestampDisabled(self, element, flags):
        if self.trip is not None:
            LOG.info(f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an open trip, closing it now')
            self.trip = None
        self.trip = Trip(self.vehicle, datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0), self.lastParkingPositionLatitude,
                         self.lastParkingPositionLongitude, None, None)
        self.trip.start_location = locationFromLatLon(self.session, self.lastParkingPositionLatitude, self.lastParkingPositionLongitude)

        if 'maintenanceStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['maintenanceStatus'].enabled:
            maintenanceStatus = self.vehicle.weConnectVehicle.statuses['maintenanceStatus']
            if maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km is not None:
                self.trip.start_mileage_km = maintenanceStatus.mileage_km.value

        self.session.add(self.trip)
        LOG.info(f'Vehicle {self.vehicle.vin} started a trip')

    def __onCarCapturedTimestampChange(self, element, flags):
        parkingPosition = self.vehicle.weConnectVehicle.statuses['parkingPosition']
        if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
            self.lastParkingPositionTimestamp = parkingPosition.carCapturedTimestamp.value
        if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
            self.lastParkingPositionLatitude = parkingPosition.latitude.value
            self.lastParkingPositionLongitude = parkingPosition.longitude.value
        if self.trip is not None:
            if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                self.trip.endDate = parkingPosition.carCapturedTimestamp.value
            if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.trip.destination_position_latitude = parkingPosition.latitude.value
                self.trip.destination_position_longitude = parkingPosition.longitude.value
                self.trip.destination_location = locationFromLatLon(self.session, parkingPosition.latitude.value, parkingPosition.longitude.value)

            if 'maintenanceStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['maintenanceStatus'].enabled:
                maintenanceStatus = self.vehicle.weConnectVehicle.statuses['maintenanceStatus']
                if maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km is not None:
                    self.trip.end_mileage_km = maintenanceStatus.mileage_km.value

            self.trip = None

            LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
        else:
            if flags is not None:
                LOG.info(f'Vehicle {self.vehicle.vin} provides a parking position, but no trip was started (this is ok during startup)')

    def commit(self):
        pass
