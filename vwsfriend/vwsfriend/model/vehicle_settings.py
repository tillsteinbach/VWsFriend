
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base


class VecicleSettings(Base):
    __tablename__ = 'vehicle_settings'
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'), primary_key=True)
    vehicle = relationship("Vehicle")

    primary_capacity = Column(Integer)
    primary_wltp_range = Column(Integer)
    secondary_capacity = Column(Integer)
    secondary_wltp_range = Column(Integer)

    def __init__(self, vehicle):
        self.vehicle = vehicle
