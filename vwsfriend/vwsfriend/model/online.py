from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class Online(Base):
    __tablename__ = 'onlinestates'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'onlineTime'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    onlineTime = Column(DatetimeDecorator)
    offlineTime = Column(DatetimeDecorator)
    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, onlineTime, offlineTime):
        self.vehicle = vehicle
        self.onlineTime = onlineTime
        self.offlineTime = offlineTime
