import logging
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError

from vwsfriend.model.battery import Battery

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class BatteryAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = session.merge(vehicle)
        self.battery = session.query(Battery).filter(and_(Battery.vehicle == vehicle,
                                                          Battery.carCapturedTimestamp.isnot(None))).order_by(Battery.carCapturedTimestamp.desc()).first()

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('charging', 'batteryStatus') \
                    and self.vehicle.weConnectVehicle.domains['charging']['batteryStatus'].enabled:
                self.vehicle.weConnectVehicle.domains['charging']['batteryStatus'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                                    onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(self.vehicle.weConnectVehicle.domains['charging']['batteryStatus'].carCapturedTimestamp, None)

    def __onCarCapturedTimestampChange(self, element, flags):
        if element is not None and element.value is not None:
            batteryStatus = self.vehicle.weConnectVehicle.domains['charging']['batteryStatus']
            current_currentSOC_pct = batteryStatus.currentSOC_pct.value
            current_cruisingRangeElectric_km = batteryStatus.cruisingRangeElectric_km.value

            if self.battery is not None:
                try:
                    self.session.refresh(self.battery)
                except ObjectDeletedError:
                    LOG.warning('Last battery entry was deleted')
                    self.battery = self.session.query(Battery).filter(and_(Battery.vehicle == self.vehicle,
                                                                           Battery.carCapturedTimestamp.isnot(None)))\
                        .order_by(Battery.carCapturedTimestamp.desc()).first()

            if self.battery is None or (self.battery.carCapturedTimestamp != batteryStatus.carCapturedTimestamp.value and (
                    self.battery.currentSOC_pct != current_currentSOC_pct
                    or self.battery.cruisingRangeElectric_km != current_cruisingRangeElectric_km)):

                if self.battery is not None and self.battery.carCapturedTimestamp > element.value:
                    LOG.warning('carCapturedTimestamp (%s) provided by batteryStatus is older than previously recorded carCapturedTimestamp (%s)',
                                element.value, self.battery.carCapturedTimestamp)

                self.battery = Battery(self.vehicle, batteryStatus.carCapturedTimestamp.value, current_currentSOC_pct, current_cruisingRangeElectric_km)
                with self.session.begin_nested():
                    try:
                        self.session.add(self.battery)
                    except IntegrityError as err:
                        LOG.warning('Could not add battery entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                self.session.commit()

    def commit(self):
        self.session.commit()
