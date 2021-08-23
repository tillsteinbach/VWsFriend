from sqlalchemy import and_

from vwsfriend.model.battery import Battery

from weconnect.addressable import AddressableLeaf


class BatteryAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.battery = session.query(Battery).filter(and_(Battery.vehicle == vehicle,
                                                          Battery.carCapturedTimestamp.isnot(None))).order_by(Battery.carCapturedTimestamp.desc()).first()

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'batteryStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['batteryStatus'].enabled:
                self.vehicle.weConnectVehicle.statuses['batteryStatus'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                         AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                         onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(None, None)

    def __onCarCapturedTimestampChange(self, element, flags):
        batteryStatus = self.vehicle.weConnectVehicle.statuses['batteryStatus']
        current_currentSOC_pct = batteryStatus.currentSOC_pct.value
        current_cruisingRangeElectric_km = batteryStatus.cruisingRangeElectric_km.value

        if self.battery is None or (self.battery.carCapturedTimestamp != batteryStatus.carCapturedTimestamp.value and (
                self.battery.currentSOC_pct != current_currentSOC_pct
                or self.battery.cruisingRangeElectric_km != current_cruisingRangeElectric_km)):

            self.battery = Battery(self.vehicle, batteryStatus.carCapturedTimestamp.value, current_currentSOC_pct, current_cruisingRangeElectric_km)
            self.session.add(self.battery)

    def commit(self):
        pass
