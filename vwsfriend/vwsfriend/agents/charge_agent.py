import logging
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from vwsfriend.model.charge import Charge
from vwsfriend.model.charging_session import ChargingSession, ACDC
from vwsfriend.util.location_util import locationFromLatLonWithGeofence, chargerFromLatLonWithGeofence
from vwsfriend.privacy import Privacy

from weconnect.addressable import AddressableLeaf
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.plug_status import PlugStatus

LOG = logging.getLogger("VWsFriend")


class ChargeAgent():
    def __init__(self, session, vehicle, privacy):
        self.session = session
        self.vehicle = vehicle
        self.privacy = privacy
        if Privacy.NO_LOCATIONS in self.privacy:
            LOG.info(f'Privacy option \'no-locations\' is set. Vehicle {self.vehicle.vin} will not record charging locations')
        self.charge = session.query(Charge).filter(and_(Charge.vehicle == vehicle, Charge.carCapturedTimestamp.isnot(None))
                                                   ).order_by(Charge.carCapturedTimestamp.desc()).first()
        self.chargingSession = None
        self.previousChargingSession = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('charging', 'chargingStatus') \
                    and self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].enabled:
                self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].carCapturedTimestamp.addObserver(
                    self.__onChargingStatusCarCapturedTimestampChange,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)
                self.__onChargingStatusCarCapturedTimestampChange(None, None)

                self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].chargingState.addObserver(self.__onChargingStateChange,
                                                                                                              AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                              onUpdateComplete=True)
                self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].chargePower_kW.addObserver(self.__onChargePowerChange,
                                                                                                               AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                               onUpdateComplete=True)

                # If the vehicle is charging check if you can catch up an open charging session:
                if self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].chargingState.enabled \
                        and self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].chargingState.value == ChargingStatus.ChargingState.CHARGING:
                    chargingSession = session.query(ChargingSession).filter(ChargingSession.vehicle == vehicle).order_by(ChargingSession.started.desc()).first()
                    if chargingSession is not None and not chargingSession.isClosed():
                        self.chargingSession = chargingSession
                        LOG.info('Vehicle is charging and an open charging session entry was found in the database. This session will be continued.')
                    else:
                        LOG.warning('Vehicle is charging but no open charging session entry was found in the database. This session cannot be recorded.')

            if self.vehicle.weConnectVehicle.statusExists('charging', 'plugStatus') \
                    and self.vehicle.weConnectVehicle.domains['charging']['plugStatus'].enabled:
                self.vehicle.weConnectVehicle.domains['charging']['plugStatus'].plugConnectionState.addObserver(self.__onPlugConnectionStateChange,
                                                                                                                AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                                onUpdateComplete=True)
                self.vehicle.weConnectVehicle.domains['charging']['plugStatus'].plugLockState.addObserver(self.__onPlugLockStateChange,
                                                                                                          AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                          onUpdateComplete=True)

    def __onChargingStatusCarCapturedTimestampChange(self, element, flags):
        if element is not None and element.value is not None:
            chargeStatus = self.vehicle.weConnectVehicle.domains['charging']['chargingStatus']
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
                try:
                    with self.session.begin_nested():
                        self.session.add(self.charge)
                    self.session.commit()
                except IntegrityError as err:
                    LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)

    def __onChargingStateChange(self, element, flags):  # noqa: C901
        chargeStatus = self.vehicle.weConnectVehicle.domains['charging']['chargingStatus']
        if element.value == ChargingStatus.ChargingState.CHARGING:
            if self.chargingSession is None or self.chargingSession.isClosed():
                self.previousChargingSession = self.chargingSession
                self.chargingSession = ChargingSession(vehicle=self.vehicle)
                try:
                    with self.session.begin_nested():
                        self.session.add(self.chargingSession)
                    self.session.commit()
                except IntegrityError:
                    LOG.warning('Could not add charging session entry to the database, this is usually due to an error in the WeConnect API')
            if not self.chargingSession.wasStarted():
                self.chargingSession.started = chargeStatus.carCapturedTimestamp.value
            # also write start SoC
            if self.chargingSession is not None and self.chargingSession.startSOC_pct is None \
                    and self.vehicle.weConnectVehicle.statusExists('charging', 'batteryStatus'):
                batteryStatus = self.vehicle.weConnectVehicle.domains['charging']['batteryStatus']
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
                        and self.vehicle.weConnectVehicle.statusExists('charging', 'batteryStatus'):
                    batteryStatus = self.vehicle.weConnectVehicle.domains['charging']['batteryStatus']
                    if batteryStatus.enabled and batteryStatus.currentSOC_pct.enabled:
                        self.chargingSession.endSOC_pct = batteryStatus.currentSOC_pct.value

                # also write position if available
                self.updatePosition()

                # also write milage if available
                self.updateMileage()

    def __onPlugConnectionStateChange(self, element, flags):
        plugStatus = self.vehicle.weConnectVehicle.domains['charging']['plugStatus']
        if element.value == PlugStatus.PlugConnectionState.CONNECTED:
            if self.chargingSession is None or self.chargingSession.isClosed():
                self.previousChargingSession = self.chargingSession
                self.chargingSession = ChargingSession(vehicle=self.vehicle)
                try:
                    with self.session.begin_nested():
                        self.session.add(self.chargingSession)
                    self.session.commit()
                except IntegrityError as err:
                    LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
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
        plugStatus = self.vehicle.weConnectVehicle.domains['charging']['plugStatus']
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
        if self.chargingSession is not None and self.chargingSession.isChargingState()\
                and (self.chargingSession.maximumChargePower_kW is None or element.value > self.chargingSession.maximumChargePower_kW):
            self.chargingSession.maximumChargePower_kW = element.value

    def updatePosition(self):
        if Privacy.NO_LOCATIONS not in self.privacy:
            if self.vehicle.weConnectVehicle.statusExists('parking', 'parkingPosition'):
                parkingPosition = self.vehicle.weConnectVehicle.domains['parking']['parkingPosition']
                if self.chargingSession is not None and parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                        and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                    self.chargingSession.position_latitude = parkingPosition.latitude.value
                    self.chargingSession.position_longitude = parkingPosition.longitude.value
                    if self.chargingSession.location is None:
                        self.chargingSession.location = locationFromLatLonWithGeofence(self.session, parkingPosition.latitude.value,
                                                                                       parkingPosition.longitude.value)
                    if self.chargingSession.charger is None:
                        self.chargingSession.charger = chargerFromLatLonWithGeofence(weConnect=self.vehicle.weConnectVehicle.weConnect, session=self.session,
                                                                                     latitude=round(parkingPosition.latitude.value, 4),
                                                                                     longitude=round(parkingPosition.longitude.value, 4), searchRadius=100)

    def updateMileage(self):
        if self.vehicle.weConnectVehicle.statusExists('measurements', 'odometerStatus'):
            odometerMeasurement = self.vehicle.weConnectVehicle.domains['measurements']['odometerStatus']
            if self.chargingSession is not None and odometerMeasurement.odometer.enabled and odometerMeasurement.odometer.value is not None:
                self.chargingSession.mileage_km = odometerMeasurement.odometer.value

    def commit(self):
        pass
