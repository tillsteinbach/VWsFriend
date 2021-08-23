from sqlalchemy import and_

from vwsfriend.model.charge import Charge
from vwsfriend.model.charging_session import ChargingSession, ACDC
from vwsfriend.util.location_util import locationFromLatLon, chargerFromLatLon

from weconnect.addressable import AddressableLeaf
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.plug_status import PlugStatus


class ChargeAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = vehicle
        self.charge = session.query(Charge).filter(and_(Charge.vehicle == vehicle, Charge.carCapturedTimestamp.isnot(None))
                                                   ).order_by(Charge.carCapturedTimestamp.desc()).first()
        self.chargingSession = None
        self.previousChargingSession = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if 'chargingStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['chargingStatus'].enabled:
                self.vehicle.weConnectVehicle.statuses['chargingStatus'].carCapturedTimestamp.addObserver(self.__onChargingStatusCarCapturedTimestampChange,
                                                                                                          AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                          onUpdateComplete=True)
                self.__onChargingStatusCarCapturedTimestampChange(None, None)

                self.vehicle.weConnectVehicle.statuses['chargingStatus'].chargingState.addObserver(self.__onChargingStateChange,
                                                                                                   AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                   onUpdateComplete=True)
                self.vehicle.weConnectVehicle.statuses['chargingStatus'].chargePower_kW.addObserver(self.__onChargePowerChange,
                                                                                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                    onUpdateComplete=True)

            if 'plugStatus' in self.vehicle.weConnectVehicle.statuses and self.vehicle.weConnectVehicle.statuses['plugStatus'].enabled:
                self.vehicle.weConnectVehicle.statuses['plugStatus'].plugConnectionState.addObserver(self.__onPlugConnectionStateChange,
                                                                                                     AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                     onUpdateComplete=True)
                self.vehicle.weConnectVehicle.statuses['plugStatus'].plugLockState.addObserver(self.__onPlugLockStateChange,
                                                                                               AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                               onUpdateComplete=True)

    def __onChargingStatusCarCapturedTimestampChange(self, element, flags):
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

            self.charge = Charge(self.vehicle, chargeStatus.carCapturedTimestamp.value, current_remainingChargingTimeToComplete_min, current_chargingState,
                                 current_chargeMode, current_chargePower_kW, current_chargeRate_kmph)
            self.session.add(self.charge)

    def __onChargingStateChange(self, element, flags):  # noqa: C901
        chargeStatus = self.vehicle.weConnectVehicle.statuses['chargingStatus']
        if element.value == ChargingStatus.ChargingState.CHARGING:
            if self.chargingSession is None or self.chargingSession.isClosed():
                self.previousChargingSession = self.chargingSession
                self.chargingSession = ChargingSession(vehicle=self.vehicle)
                self.session.add(self.chargingSession)
            if not self.chargingSession.wasStarted():
                self.chargingSession.started = chargeStatus.carCapturedTimestamp.value
            # also write start SoC
            if self.chargingSession is not None and self.chargingSession.startSOC_pct is None \
                    and 'batteryStatus' in self.vehicle.weConnectVehicle.statuses:
                batteryStatus = self.vehicle.weConnectVehicle.statuses['batteryStatus']
                if batteryStatus.enabled and batteryStatus.currentSOC_pct.enabled:
                    self.chargingSession.startSOC_pct = batteryStatus.currentSOC_pct.value

            # also write position if available
            self.updatePosition()

            # also write milage if available
            self.updateMileage()
        elif element.value in [ChargingStatus.ChargingState.OFF, ChargingStatus.ChargingState.READY_FOR_CHARGING]:
            if self.chargingSession is not None and self.chargingSession.isChargingState():
                self.chargingSession.ended = chargeStatus.carCapturedTimestamp.value

                if self.chargingSession.maximumChargePower_kW is not None:
                    if self.chargingSession.maximumChargePower_kW > 11:
                        self.chargingSession.acdc = ACDC.DC
                    else:
                        self.chargingSession.acdc = ACDC.AC
                # also write end SoC
                if self.chargingSession is not None and self.chargingSession.endSOC_pct is None \
                        and 'batteryStatus' in self.vehicle.weConnectVehicle.statuses:
                    batteryStatus = self.vehicle.weConnectVehicle.statuses['batteryStatus']
                    if batteryStatus.enabled and batteryStatus.currentSOC_pct.enabled:
                        self.chargingSession.endSOC_pct = batteryStatus.currentSOC_pct.value

                # also write position if available
                self.updatePosition()

                # also write milage if available
                self.updateMileage()

    def __onPlugConnectionStateChange(self, element, flags):
        plugStatus = self.vehicle.weConnectVehicle.statuses['plugStatus']
        if element.value == PlugStatus.PlugConnectionState.CONNECTED:
            if self.chargingSession is None or self.chargingSession.isClosed():
                self.previousChargingSession = self.chargingSession
                self.chargingSession = ChargingSession(vehicle=self.vehicle)
                self.session.add(self.chargingSession)
            if self.chargingSession.connected is None:
                self.chargingSession.connected = plugStatus.carCapturedTimestamp.value
            # also write position if available
            self.updatePosition()
            # also write milage if available
            self.updateMileage()
        elif element.value == PlugStatus.PlugConnectionState.DISCONNECTED:
            if self.chargingSession is not None and self.chargingSession.isConnectedState():
                self.chargingSession.disconnected = plugStatus.carCapturedTimestamp.value
            # also write position if available
            self.updatePosition()
            # also write milage if available
            self.updateMileage()

    def __onPlugLockStateChange(self, element, flags):
        plugStatus = self.vehicle.weConnectVehicle.statuses['plugStatus']
        if element.value == PlugStatus.PlugLockState.LOCKED:
            if self.chargingSession is None or self.chargingSession.isClosed():
                self.previousChargingSession = self.chargingSession
                self.chargingSession = ChargingSession(vehicle=self.vehicle)
                self.session.add(self.chargingSession)
            if self.chargingSession.locked is None:
                self.chargingSession.locked = plugStatus.carCapturedTimestamp.value
            # also write position if available
            self.updatePosition()
            # also write milage if available
            self.updateMileage()
        elif element.value == PlugStatus.PlugLockState.UNLOCKED:
            if self.chargingSession is not None and self.chargingSession.isLockedState():
                self.chargingSession.unlocked = plugStatus.carCapturedTimestamp.value
            # also write position if available
            self.updatePosition()
            # also write milage if available
            self.updateMileage()

    def __onChargePowerChange(self, element, flags):
        if self.chargingSession.isChargingState() and self.chargingSession is not None \
                and (self.chargingSession.maximumChargePower_kW is None or element.value > self.chargingSession.maximumChargePower_kW):
            self.chargingSession.maximumChargePower_kW = element.value

    def updatePosition(self):
        if 'parkingPosition' in self.vehicle.weConnectVehicle.statuses:
            parkingPosition = self.vehicle.weConnectVehicle.statuses['parkingPosition']
            if self.chargingSession is not None and parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.chargingSession.position_latitude = parkingPosition.latitude.value
                self.chargingSession.position_longitude = parkingPosition.longitude.value
                if self.chargingSession.location is None:
                    self.chargingSession.location = locationFromLatLon(self.session, parkingPosition.latitude.value, parkingPosition.longitude.value)
                if self.chargingSession.charger is None:
                    self.chargingSession.charger = chargerFromLatLon(weConnect=self.vehicle.weConnectVehicle.weConnect, session=self.session,
                                                                     latitude=parkingPosition.latitude.value, longitude=parkingPosition.longitude.value,
                                                                     searchRadius=100)

    def updateMileage(self):
        if 'maintenanceStatus' in self.vehicle.weConnectVehicle.statuses:
            maintenanceStatus = self.vehicle.weConnectVehicle.statuses['maintenanceStatus']
            if self.chargingSession is not None and maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km.value is not None:
                self.chargingSession.mileage_km = maintenanceStatus.mileage_km.value

    def commit(self):
        pass
