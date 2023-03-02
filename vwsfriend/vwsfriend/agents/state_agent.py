from enum import Enum, auto
from datetime import datetime, timezone, timedelta
import logging

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError

from vwsfriend.model.online import Online

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class StateAgent():
    def __init__(self, session, vehicle, updateInterval):
        self.session = session
        self.vehicle = session.merge(vehicle)
        self.onlineTimeout = (updateInterval * 2) + 30
        self.offlineTimeout = (updateInterval * 2) + 30
        # The offline timeout must be at least 10 minutes plus 30 seconds as this is the update frequency of data for some cars.
        if self.offlineTimeout < 630:
            self.offlineTimeout = 630
        self.onlineState = None
        self.online = session.query(Online).filter(and_(Online.vehicle == vehicle, Online.onlineTime.isnot(None))).order_by(Online.onlineTime.desc()).first()
        # If the last record in the database is completed we are not online right now
        if self.online is None or self.online.offlineTime is not None:
            self.online = None
            self.onlineState = StateAgent.OnlineState.OFFLINE
        else:
            self.onlineState = StateAgent.OnlineState.ONLINE
            LOG.warning(f'Vehicle {vehicle.vin} is still online in database. Looks like the session was closed when the vehicle was still online!')
        self.lastCarCapturedTimestamp = None
        self.earliestCarCapturedTimestampInInterval = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            for domain in self.vehicle.weConnectVehicle.domains.values():
                for status in domain.values():
                    status.carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                            onUpdateComplete=True)
                    self.__onCarCapturedTimestampChange(element=status.carCapturedTimestamp, flags=None)

    def __onCarCapturedTimestampChange(self, element, flags):
        if element.enabled and (self.lastCarCapturedTimestamp is None or self.lastCarCapturedTimestamp < element.value):
            self.lastCarCapturedTimestamp = element.value
        if self.onlineState == StateAgent.OnlineState.OFFLINE:
            if element.enabled and (self.earliestCarCapturedTimestampInInterval is None or self.earliestCarCapturedTimestampInInterval > element.value) \
                    and (element.value + timedelta(seconds=self.onlineTimeout)) > datetime.utcnow().replace(tzinfo=timezone.utc):
                self.earliestCarCapturedTimestampInInterval = element.value

    def checkOnlineOffline(self):  # noqa: C901
        if self.online is not None:
            try:
                self.session.refresh(self.online)
            except ObjectDeletedError:
                LOG.warning('Last online entry was deleted')
                self.online = self.session.query(Online).filter(and_(Online.vehicle == self.vehicle,
                                                                     Online.onlineTime.isnot(None))).order_by(Online.onlineTime.desc()).first()
            except InvalidRequestError:
                LOG.warning('Last online entry was not persisted')
                self.online = self.session.query(Online).filter(and_(Online.vehicle == self.vehicle,
                                                                     Online.onlineTime.isnot(None))).order_by(Online.onlineTime.desc()).first()
        if self.onlineState == StateAgent.OnlineState.ONLINE:
            if self.online is not None and self.lastCarCapturedTimestamp is not None \
                    and (self.lastCarCapturedTimestamp + timedelta(seconds=self.offlineTimeout)) < datetime.utcnow().replace(tzinfo=timezone.utc):
                LOG.info(f'Vehicle {self.vehicle.vin} went offline')
                self.onlineState = StateAgent.OnlineState.OFFLINE
                self.vehicle.online = False
                with self.session.begin_nested():
                    self.online.offlineTime = self.lastCarCapturedTimestamp
                self.session.commit()
                self.online = None
                self.lastCarCapturedTimestamp = None
            else:
                if self.vehicle.lastChange is None or (self.lastCarCapturedTimestamp > self.vehicle.lastChange.replace(tzinfo=timezone.utc)):
                    self.vehicle.lastChange = self.lastCarCapturedTimestamp
        else:
            # When online now but now record add the record
            if self.online is None and self.earliestCarCapturedTimestampInInterval is not None:
                LOG.info(f'Vehicle {self.vehicle.vin} went online')
                self.onlineState = StateAgent.OnlineState.ONLINE
                with self.session.begin_nested():
                    self.vehicle.online = True
                    if self.vehicle.lastChange is None or (self.lastCarCapturedTimestamp > self.vehicle.lastChange.replace(tzinfo=timezone.utc)):
                        self.vehicle.lastChange = self.lastCarCapturedTimestamp
                self.session.commit()
                self.online = Online(self.vehicle, onlineTime=self.earliestCarCapturedTimestampInInterval, offlineTime=None)
                with self.session.begin_nested():
                    try:
                        self.session.add(self.online)
                    except IntegrityError as err:
                        LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                self.session.commit()
                self.earliestCarCapturedTimestampInInterval = None

    def commit(self):
        self.checkOnlineOffline()
        with self.session.begin_nested():
            self.vehicle.lastUpdate = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.session.commit()

    class OnlineState(Enum):
        ONLINE = auto()
        OFFLINE = auto()
