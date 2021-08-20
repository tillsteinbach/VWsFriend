from enum import Enum, auto
from datetime import datetime, timezone, timedelta
import logging

from sqlalchemy import and_

from vwsfriend.model.online import Online

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class StateAgent():
    def __init__(self, session, vehicle, updateInterval):
        self.session = session
        self.vehicle = vehicle
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
            for status in self.vehicle.weConnectVehicle.statuses.values():
                status.carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(element=status.carCapturedTimestamp, flags=None)

    def __onCarCapturedTimestampChange(self, element, flags):
        if element.enabled and (self.lastCarCapturedTimestamp is None or self.lastCarCapturedTimestamp < element.value):
            self.lastCarCapturedTimestamp = element.value
        if self.onlineState == StateAgent.OnlineState.OFFLINE:
            if element.enabled and (self.earliestCarCapturedTimestampInInterval is None or self.earliestCarCapturedTimestampInInterval > element.value) \
                    and (element.value + timedelta(seconds=self.onlineTimeout)) > datetime.utcnow().replace(tzinfo=timezone.utc):
                self.earliestCarCapturedTimestampInInterval = element.value

    def checkOnlineOffline(self):
        if self.onlineState == StateAgent.OnlineState.ONLINE:
            if self.online is not None and (self.lastCarCapturedTimestamp + timedelta(seconds=self.offlineTimeout)) \
                    < datetime.utcnow().replace(tzinfo=timezone.utc):
                LOG.info(f'Vehicle {self.vehicle.vin} went offline')
                self.onlineState = StateAgent.OnlineState.OFFLINE
                self.vehicle.online = False
                self.online.offlineTime = self.lastCarCapturedTimestamp
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
                self.vehicle.online = True
                if self.vehicle.lastChange is None or (self.lastCarCapturedTimestamp > self.vehicle.lastChange.replace(tzinfo=timezone.utc)):
                    self.vehicle.lastChange = self.lastCarCapturedTimestamp
                self.online = Online(self.vehicle, onlineTime=self.earliestCarCapturedTimestampInInterval, offlineTime=None)
                self.session.add(self.online)
                self.earliestCarCapturedTimestampInInterval = None

    def commit(self):
        self.checkOnlineOffline()
        self.vehicle.lastUpdate = datetime.utcnow().replace(tzinfo=timezone.utc)

    class OnlineState(Enum):
        ONLINE = auto()
        OFFLINE = auto()
