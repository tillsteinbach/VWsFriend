from datetime import datetime, timezone, timedelta
from vwsfriend.model.online import Online

from weconnect.addressable import AddressableLeaf


class StateAgent():
    def __init__(self, session, vehicle, updateInterval):
        self.session = session
        self.vehicle = vehicle
        self.updateInterval = updateInterval
        self.online = session.query(Online).filter(Online.vehicle == vehicle).order_by(Online.onlineTime.desc()).first()
        # If the last record in the database is completed we are not online right now
        if self.online is not None and self.online.offlineTime is not None:
            self.online = None
        self.lastCarCapturedTimestamp = None

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            for status in self.vehicle.weConnectVehicle.statuses.values():
                status.carCapturedTimestamp.addObserver(self.__onCarCapturedTimestampChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True)
                if status.carCapturedTimestamp.enabled and (self.lastCarCapturedTimestamp is None or self.lastCarCapturedTimestamp < status.carCapturedTimestamp.value):
                    self.lastCarCapturedTimestamp = status.carCapturedTimestamp.value

    def __onCarCapturedTimestampChange(self, element, flags):
        if element.enabled and (self.lastCarCapturedTimestamp is None or self.lastCarCapturedTimestamp < element.value):
            self.lastCarCapturedTimestamp = element.value

    def checkOnlineOffline(self):
        if self.lastCarCapturedTimestamp is not None:
            online = True
            if (self.lastCarCapturedTimestamp + timedelta(seconds=((self.updateInterval * 2) + 30))) < datetime.utcnow().replace(tzinfo=timezone.utc):
                online = False

        if online:
            # When online now but now record add the record
            if self.online is None:
                self.online = Online(self.vehicle, onlineTime=self.lastCarCapturedTimestamp, offlineTime=None)
                self.session.add(self.online)
        else:
            # When offline but there is an open record, close the record
            if self.online is not None:
                self.online.offlineTime = self.lastCarCapturedTimestamp
                self.session.commit()
                self.online = None

    def commit(self):
        self.checkOnlineOffline()
