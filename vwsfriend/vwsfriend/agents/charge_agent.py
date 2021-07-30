from vwsfriend.model.charge import Charge

from weconnect.addressable import AddressableLeaf


class ChargeAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.charge = session.query(Charge).filter(Charge.vehicle == vehicle).order_by(Charge.carCapturedTimestamp.desc()).first()
        
        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'chargingStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['chargingStatus'].enabled:
                self.vehicle.weConnectVehicle.statuses['chargingStatus'].carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(None, None)

    def __onCarCapturedTimestampChange(self, element, flags):
        chargeStatus = self.vehicle.weConnectVehicle.statuses['chargingStatus']
        current_remainingChargingTimeToComplete_min = None
        current_chargingState = None
        current_chargeMode = None
        current_chargePower_kW = None
        current_chargeRate_kmph = None
        if chargeStatus.remainingChargingTimeToComplete_min.enabled:
            current_remainingChargingTimeToComplete_min = chargeStatus.remainingChargingTimeToComplete_min.value
        if chargeStatus.chargingState.enabled:
            current_chargingState = chargeStatus.chargingState.value
        if chargeStatus.chargeMode.enabled:
            current_chargeMode = chargeStatus.chargeMode.value
        if chargeStatus.chargePower_kW.enabled:
            current_chargePower_kW = chargeStatus.chargePower_kW.value
        if chargeStatus.chargeRate_kmph.enabled:
            current_chargeRate_kmph = chargeStatus.chargeRate_kmph.value

        if self.charge is None or (self.charge.carCapturedTimestamp != chargeStatus.carCapturedTimestamp.value and (
                self.charge.remainingChargingTimeToComplete_min != current_remainingChargingTimeToComplete_min
                or self.charge.chargingState != current_chargingState
                or self.charge.chargeMode != current_chargeMode
                or self.charge.chargePower_kW != current_chargePower_kW
                or self.charge.chargeRate_kmph != current_chargeRate_kmph)):

            self.charge = Charge(self.vehicle, chargeStatus.carCapturedTimestamp.value, current_remainingChargingTimeToComplete_min, current_chargingState, current_chargeMode, current_chargePower_kW, current_chargeRate_kmph)
            self.session.add(self.charge)

    def commit(self):
        pass
