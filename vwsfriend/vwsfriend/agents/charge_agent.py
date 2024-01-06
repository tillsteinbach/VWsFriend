import logging
from datetime import timedelta
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError

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
        self.vehicle = session.merge(vehicle)
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
                        and self.vehicle.weConnectVehicle.domains['charging']['chargingStatus'].chargingState.value in \
                        (ChargingStatus.ChargingState.CHARGING,
                         ChargingStatus.ChargingState.CONSERVATION,
                         ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING,
                         ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION,
                         ChargingStatus.ChargingState.DISCHARGING):
                    chargingSession = session.query(ChargingSession).filter(and_(ChargingSession.vehicle == vehicle, ChargingSession.started.isnot(None))
                                                                            ).order_by(ChargingSession.started.desc()).first()
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

                # If the vehicle is still connected check if you can catch up an open charging session:
                if self.chargingSession is None and self.vehicle.weConnectVehicle.domains['charging']['plugStatus'].plugConnectionState.value \
                        == PlugStatus.PlugConnectionState.CONNECTED:
                    chargingSession = session.query(ChargingSession).filter(and_(ChargingSession.vehicle == vehicle, ChargingSession.connected.isnot(None))
                                                                            ).order_by(ChargingSession.connected.desc()).first()
                    if chargingSession is not None and not chargingSession.wasDisconnected():
                        self.chargingSession = chargingSession
                        LOG.info('Vehicle is still connected and an open charging session entry was found in the database. This session will be continued.')
                    else:
                        LOG.warning('Vehicle still connected but no open charging session entry was found in the database. This session cannot be recorded.')

    def __onChargingStatusCarCapturedTimestampChange(self, element, flags):  # noqa: C901
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

            if self.charge is not None:
                try:
                    self.session.refresh(self.charge)
                except ObjectDeletedError:
                    LOG.warning('Last charge entry was deleted')
                    self.charge = self.session.query(Charge).filter(and_(Charge.vehicle == self.vehicle, Charge.carCapturedTimestamp.isnot(None))) \
                        .order_by(Charge.carCapturedTimestamp.desc()).first()
                except InvalidRequestError:
                    LOG.warning('Last charge entry was not persisted')
                    self.charge = self.session.query(Charge).filter(and_(Charge.vehicle == self.vehicle, Charge.carCapturedTimestamp.isnot(None))) \
                        .order_by(Charge.carCapturedTimestamp.desc()).first()

            if self.charge is None or (self.charge.carCapturedTimestamp != chargeStatus.carCapturedTimestamp.value and (
                    self.charge.remainingChargingTimeToComplete_min != current_remainingChargingTimeToComplete_min
                    or self.charge.chargingState != current_chargingState
                    or self.charge.chargeMode != current_chargeMode
                    or self.charge.chargePower_kW != current_chargePower_kW
                    or self.charge.chargeRate_kmph != current_chargeRate_kmph)):

                self.charge = Charge(self.vehicle, chargeStatus.carCapturedTimestamp.value, current_remainingChargingTimeToComplete_min, current_chargingState,
                                     current_chargeMode, current_chargePower_kW, current_chargeRate_kmph)
                with self.session.begin_nested():
                    try:
                        self.session.add(self.charge)
                    except IntegrityError as err:
                        LOG.warning('Could not add charge entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                self.session.commit()

    def __onChargingStateChange(self, element, flags):  # noqa: C901
        chargeStatus = self.vehicle.weConnectVehicle.domains['charging']['chargingStatus']

        if self.chargingSession is not None:
            try:
                self.session.refresh(self.chargingSession)
            except ObjectDeletedError:
                LOG.warning('Open charging session was deleted')
                self.previousChargingSession = None
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None
            except InvalidRequestError:
                LOG.warning('Last charging session was not persisted')
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None

        if element.value in [ChargingStatus.ChargingState.CHARGING, ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION,
                             ChargingStatus.ChargingState.CONSERVATION]:
            with self.session.begin_nested():
                if self.chargingSession is None or self.chargingSession.isClosed():
                    # In case this was an interrupted charging session (interrupt no longer than  or loger if conservation), continue by erasing end time
                    interruptTimeHours = 24
                    if element.value in [ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION, ChargingStatus.ChargingState.CONSERVATION]:
                        interruptTimeHours = 300
                    if self.chargingSession is not None and not self.chargingSession.wasDisconnected() \
                            and (self.chargingSession.ended is None or chargeStatus.carCapturedTimestamp.value is None
                                 or self.chargingSession.ended > (chargeStatus.carCapturedTimestamp.value - timedelta(hours=interruptTimeHours))):
                        self.chargingSession.ended = None
                        self.chargingSession.endSOC_pct = None
                    else:
                        self.previousChargingSession = self.chargingSession
                        self.chargingSession = ChargingSession(vehicle=self.vehicle)
                        try:
                            self.session.add(self.chargingSession)
                        except IntegrityError:
                            LOG.warning('Could not add charging session entry to the database, this is usually due to an error in the WeConnect API')
                            self.chargingSession = None
            self.session.commit()
            if self.chargingSession is not None:
                with self.session.begin_nested():
                    if not self.chargingSession.wasStarted():
                        self.chargingSession.started = chargeStatus.carCapturedTimestamp.value
                    # also write start SoC
                    if self.chargingSession is not None and self.chargingSession.startSOC_pct is None \
                            and self.vehicle.weConnectVehicle.statusExists('charging', 'batteryStatus'):
                        batteryStatus = self.vehicle.weConnectVehicle.domains['charging']['batteryStatus']
                        if batteryStatus.enabled and batteryStatus.currentSOC_pct.enabled:
                            self.chargingSession.startSOC_pct = batteryStatus.currentSOC_pct.value
                    # also write start charge type if available and not already set
                    if self.chargingSession is not None and self.chargingSession.acdc is None \
                            and chargeStatus.chargeType.enabled:
                        if chargeStatus.chargeType.value == ChargingStatus.ChargeType.AC:
                            self.chargingSession.acdc = ACDC.AC
                        elif chargeStatus.chargeType.value == ChargingStatus.ChargeType.DC:
                            self.chargingSession.acdc = ACDC.DC

                    # also write position if available
                    self.updatePosition()

                    # also write milage if available
                    self.updateMileage()
                self.session.commit()

        elif element.value in [ChargingStatus.ChargingState.OFF, ChargingStatus.ChargingState.READY_FOR_CHARGING,
                               ChargingStatus.ChargingState.NOT_READY_FOR_CHARGING,
                               ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING,
                               ChargingStatus.ChargingState.ERROR]:
            with self.session.begin_nested():
                if self.chargingSession is not None and self.chargingSession.isChargingState():
                    self.chargingSession.ended = chargeStatus.carCapturedTimestamp.value

                    # also write start charge type if not already set before
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
            self.session.commit()

    def __onPlugConnectionStateChange(self, element, flags):  # noqa: C901
        plugStatus = self.vehicle.weConnectVehicle.domains['charging']['plugStatus']

        if self.chargingSession is not None:
            try:
                self.session.refresh(self.chargingSession)
            except ObjectDeletedError:
                LOG.warning('Open charging session was deleted')
                self.previousChargingSession = None
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None
            except InvalidRequestError:
                LOG.warning('Last charging session was not persisted')
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None

        if element.value == PlugStatus.PlugConnectionState.CONNECTED:
            with self.session.begin_nested():
                if self.chargingSession is None or self.chargingSession.isClosed():
                    self.previousChargingSession = self.chargingSession
                    self.chargingSession = ChargingSession(vehicle=self.vehicle)
                    try:
                        self.session.add(self.chargingSession)
                    except IntegrityError as err:
                        LOG.warning('Could not add charging session entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                        self.chargingSession = None
                if self.chargingSession is not None:
                    if self.chargingSession.connected is None:
                        self.chargingSession.connected = plugStatus.carCapturedTimestamp.value
                    # also write position if available
                    self.updatePosition()
                    # also write milage if available
                    self.updateMileage()
            self.session.commit()

        elif element.value == PlugStatus.PlugConnectionState.DISCONNECTED:
            with self.session.begin_nested():
                if self.chargingSession is not None and self.chargingSession.isConnectedState():
                    self.chargingSession.disconnected = plugStatus.carCapturedTimestamp.value

                if self.chargingSession is not None:
                    # also write position if available
                    self.updatePosition()
                    # also write milage if available
                    self.updateMileage()
            self.session.commit()

    def __onPlugLockStateChange(self, element, flags):  # noqa: C901
        plugStatus = self.vehicle.weConnectVehicle.domains['charging']['plugStatus']

        if self.chargingSession is not None:
            try:
                self.session.refresh(self.chargingSession)
            except ObjectDeletedError:
                LOG.warning('Open charging session was deleted')
                self.previousChargingSession = None
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None
            except InvalidRequestError:
                LOG.warning('Last charging session was not persisted')
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None

        if element.value == PlugStatus.PlugLockState.LOCKED:
            with self.session.begin_nested():
                if self.chargingSession is None or self.chargingSession.isClosed():
                    # In case this was an interrupted charging session (interrupt no longer than 24hours), continue by erasing end time
                    if self.chargingSession is not None and not self.chargingSession.wasDisconnected() \
                            and (self.chargingSession.unlocked is None or plugStatus.carCapturedTimestamp.value is None
                                 or self.chargingSession.unlocked > (plugStatus.carCapturedTimestamp.value - timedelta(hours=24))):
                        self.chargingSession.unlocked = None
                    else:
                        self.previousChargingSession = self.chargingSession
                        self.chargingSession = ChargingSession(vehicle=self.vehicle)
                        try:
                            self.session.add(self.chargingSession)
                        except IntegrityError as err:
                            LOG.warning('Could not add charging session entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                            self.chargingSession = None
                if self.chargingSession is not None:
                    if self.chargingSession.locked is None:
                        self.chargingSession.locked = plugStatus.carCapturedTimestamp.value
                    # also write position if available
                    self.updatePosition()
                    # also write milage if available
                    self.updateMileage()
            self.session.commit()

        elif element.value == PlugStatus.PlugLockState.UNLOCKED:
            with self.session.begin_nested():
                if self.chargingSession is not None and self.chargingSession.isLockedState():
                    self.chargingSession.unlocked = plugStatus.carCapturedTimestamp.value
                if self.chargingSession is not None:
                    # also write position if available
                    self.updatePosition()
                    # also write milage if available
                    self.updateMileage()
            self.session.commit()

    def __onChargePowerChange(self, element, flags):
        if self.chargingSession is not None:
            try:
                self.session.refresh(self.chargingSession)
            except ObjectDeletedError:
                LOG.warning('Open charging session was deleted')
                self.previousChargingSession = None
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None
            except InvalidRequestError:
                LOG.warning('Last charging session was not persisted')
                chargingSession = self.session.query(ChargingSession).filter(ChargingSession.vehicle == self.vehicle) \
                    .order_by(ChargingSession.started.desc()).first()
                if chargingSession is not None and not chargingSession.isClosed():
                    self.chargingSession = chargingSession
                else:
                    self.chargingSession = None

        if self.chargingSession is not None and self.chargingSession.isChargingState()\
                and (self.chargingSession.maximumChargePower_kW is None or element.value > self.chargingSession.maximumChargePower_kW):
            with self.session.begin_nested():
                self.chargingSession.maximumChargePower_kW = element.value
            self.session.commit()

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
        self.session.commit()
