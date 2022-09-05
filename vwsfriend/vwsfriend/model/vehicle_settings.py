
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base


class VehicleSettings(Base):
    __tablename__ = 'vehicle_settings'
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'), primary_key=True)
    vehicle = relationship("Vehicle", back_populates="settings")

    primary_capacity = Column(Integer)
    primary_capacity_total = Column(Integer)
    primary_wltp_range = Column(Integer)
    secondary_capacity = Column(Integer)
    secondary_capacity_total = Column(Integer)
    secondary_wltp_range = Column(Integer)
    timezone = Column(String(256))
    sorting_order = Column(Integer)
    hide = Column(Boolean)

    def __init__(self, vehicle):
        self.vehicle = vehicle
