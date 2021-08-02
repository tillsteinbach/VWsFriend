import logging

from vwsfriend.model.trip import Trip
from vwsfriend.util.location_util import locationFromLatLon

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class TripAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.trip = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'parkingPosition' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['parkingPosition'].enabled:
                self.vehicle.weConnectVehicle.statuses['parkingPosition'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                           AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                           onUpdateComplete=True)

    def __onCarCapturedTimestampChange(self, element, flags):
        parkingPosition = self.vehicle.weConnectVehicle.statuses['parkingPosition']

        self.trip = Trip(self.vehicle, None, None, None, None, None)
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

        self.session.add(self.trip)
        LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')

    def commit(self):
        pass
