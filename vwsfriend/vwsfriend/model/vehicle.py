from sqlalchemy import Column, String, Enum, Boolean
from sqlalchemy.orm import relationship

from weconnect.addressable import AddressableLeaf
from weconnect.elements.range_status import RangeStatus

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class Vehicle(Base):
    __tablename__ = 'vehicles'
    vin = Column(String(17), primary_key=True)
    model = Column(String(256))
    nickname = Column(String(256))
    carType = Column(Enum(RangeStatus.CarType, length=63))
    online = Column(Boolean)
    lastUpdate = Column(DatetimeDecorator)
    lastChange = Column(DatetimeDecorator)
    settings = relationship("VehicleSettings", back_populates="vehicle", uselist=False)

    weConnectVehicle = None

    def __init__(self, vin):
        self.vin = vin

    def connect(self, weConnectVehicle):
        self.weConnectVehicle = weConnectVehicle
        self.weConnectVehicle.model.addObserver(self.__onModelChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
        if self.weConnectVehicle.model.enabled and self.model != self.weConnectVehicle.model.value:
            self.model = self.weConnectVehicle.model.value
        self.weConnectVehicle.nickname.addObserver(self.__onNicknameChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
        if self.weConnectVehicle.nickname.enabled and self.nickname != self.weConnectVehicle.nickname.value:
            self.nickname = self.weConnectVehicle.nickname.value
        if 'rangeStatus' in self.weConnectVehicle.statuses and self.weConnectVehicle.statuses['rangeStatus'].enabled:
            self.weConnectVehicle.statuses['rangeStatus'].carType.addObserver(self.__onCarTypeChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            if self.weConnectVehicle.statuses['rangeStatus'].carType.enabled:
                self.carType = self.weConnectVehicle.statuses['rangeStatus'].carType.value
            elif self.carType is None:
                self.carType = RangeStatus.CarType.UNKNOWN

    def __onModelChange(self, element, flags):
        if self.model != element.value:
            self.model = element.value

    def __onNicknameChange(self, element, flags):
        if self.nickname != element.value:
            self.nickname = element.value

    def __onCarTypeChange(self, element, flags):
        if self.carType != element.value:
            self.carType = element.value
