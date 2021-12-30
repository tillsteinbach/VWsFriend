from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from vwsfriend.model.range import Range

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class RangeAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.range = session.query(Range).filter(and_(Range.vehicle == vehicle,
                                                      Range.carCapturedTimestamp.isnot(None))).order_by(Range.carCapturedTimestamp.desc()).first()

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('fuelStatus', 'rangeStatus') \
                    and self.vehicle.weConnectVehicle.domains['fuelStatus']['rangeStatus'].enabled:
                self.vehicle.weConnectVehicle.domains['fuelStatus']['rangeStatus'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                                    onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(None, None)

    def __onCarCapturedTimestampChange(self, element, flags):
        # Check that the data to add is not too old
        if element is not None and element.value is not None and element.value > (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=7)):
            rangeStatus = self.vehicle.weConnectVehicle.domains['fuelStatus']['rangeStatus']
            current_totalRange_km = rangeStatus.totalRange_km.value
            current_primary_currentSOC_pct = None
            current_primary_remainingRange_km = None
            if rangeStatus.primaryEngine.enabled:
                current_primary_currentSOC_pct = rangeStatus.primaryEngine.currentSOC_pct.value
                current_primary_remainingRange_km = rangeStatus.primaryEngine.remainingRange_km.value
            current_secondary_currentSOC_pct = None
            current_secondary_remainingRange_km = None
            if rangeStatus.secondaryEngine.enabled:
                current_secondary_currentSOC_pct = rangeStatus.secondaryEngine.currentSOC_pct.value
                current_secondary_remainingRange_km = rangeStatus.secondaryEngine.remainingRange_km.value

            if self.range is None or (rangeStatus.carCapturedTimestamp.value is not None
                                      and self.range.carCapturedTimestamp != rangeStatus.carCapturedTimestamp.value
                                      and (self.range.totalRange_km != current_totalRange_km
                                           or self.range.primary_currentSOC_pct != current_primary_currentSOC_pct
                                           or self.range.primary_remainingRange_km != current_primary_remainingRange_km
                                           or self.range.secondary_currentSOC_pct != current_secondary_currentSOC_pct
                                           or self.range.secondary_remainingRange_km != current_secondary_remainingRange_km)):

                self.range = Range(self.vehicle, rangeStatus.carCapturedTimestamp.value, current_totalRange_km, current_primary_currentSOC_pct,
                                   current_primary_remainingRange_km, current_secondary_currentSOC_pct, current_secondary_remainingRange_km)
                try:
                    with self.session.begin_nested():
                        self.session.add(self.range)
                except IntegrityError as err:
                    LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)

    def commit(self):
        pass
