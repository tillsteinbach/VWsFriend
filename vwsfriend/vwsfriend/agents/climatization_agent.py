from sqlalchemy import and_

from vwsfriend.model.climatization import Climatization

from weconnect.addressable import AddressableLeaf


class ClimatizationAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.charge = session.query(Climatization).filter(and_(Climatization.vehicle == vehicle,
                                                               Climatization.carCapturedTimestamp.isnot(None))) \
                                                  .order_by(Climatization.carCapturedTimestamp.desc()).first()

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'climatisationStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['climatisationStatus'].enabled:
                self.vehicle.weConnectVehicle.statuses['climatisationStatus'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange,
                                                                                                               AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                               onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(None, None)

    def __onCarCapturedTimestampChange(self, element, flags):
        chargeStatus = self.vehicle.weConnectVehicle.statuses['climatisationStatus']
        current_remainingClimatisationTime_min = None
        current_climatisationState = None
        if chargeStatus.remainingClimatisationTime_min.enabled:
            current_remainingClimatisationTime_min = chargeStatus.remainingClimatisationTime_min.value
        if chargeStatus.climatisationState.enabled:
            current_climatisationState = chargeStatus.climatisationState.value

        if self.charge is None or (self.charge.carCapturedTimestamp != chargeStatus.carCapturedTimestamp.value and (
                self.charge.remainingClimatisationTime_min != current_remainingClimatisationTime_min
                or self.charge.climatisationState != current_climatisationState)):

            self.charge = Climatization(self.vehicle, chargeStatus.carCapturedTimestamp.value, current_remainingClimatisationTime_min,
                                        current_climatisationState)
            self.session.add(self.charge)

    def commit(self):
        pass
