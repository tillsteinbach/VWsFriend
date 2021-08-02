import logging

from vwsfriend.model.refuel_session import RefuelSession

from weconnect.addressable import AddressableLeaf
from weconnect.elements.range_status import RangeStatus

LOG = logging.getLogger("VWsFriend")


class RefuelAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.primary_currentSOC_pct = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'rangeStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['rangeStatus'].enabled:
                self.vehicle.weConnectVehicle.statuses['rangeStatus'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                       AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                       onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(None, None)

    def __onCarCapturedTimestampChange(self, element, flags):
        rangeStatus = self.vehicle.weConnectVehicle.statuses['rangeStatus']
        if self.vehicle.carType in [RangeStatus.CarType.HYBRID] and rangeStatus.primaryEngine.currentSOC_pct.enabled:
            current_primary_currentSOC_pct = rangeStatus.primaryEngine.currentSOC_pct.value

            mileage_km = None
            if 'maintenanceStatus' in self.vehicle.weConnectVehicle.statuses:
                maintenanceStatus = self.vehicle.weConnectVehicle.statuses['maintenanceStatus']
                if maintenanceStatus.mileage_km.enabled:
                    mileage_km = maintenanceStatus.mileage_km.value

            # Refuel event took place
            if self.primary_currentSOC_pct is not None and current_primary_currentSOC_pct > self.primary_currentSOC_pct:
                LOG.info('Vehicle %s refueled from %d percent to %d percent', self.vehicle.vin, self.primary_currentSOC_pct, current_primary_currentSOC_pct)
                self.range = RefuelSession(self.vehicle, element.value, self.primary_currentSOC_pct, current_primary_currentSOC_pct, mileage_km)
                self.session.add(self.range)
                self.primary_currentSOC_pct = current_primary_currentSOC_pct
            # SoC decreased, normal usage
            elif self.primary_currentSOC_pct is None or current_primary_currentSOC_pct < self.primary_currentSOC_pct:
                self.primary_currentSOC_pct = current_primary_currentSOC_pct

    def commit(self):
        pass
