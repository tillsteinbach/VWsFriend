from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base


class Online(Base):
    __tablename__ = 'onlinestates'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'onlineTime'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    onlineTime = Column(DateTime)
    offlineTime = Column(DateTime)
    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, onlineTime, offlineTime):
        self.vehicle = vehicle
        self.onlineTime = onlineTime
        self.offlineTime = offlineTime
