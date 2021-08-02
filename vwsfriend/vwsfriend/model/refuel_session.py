from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base


class RefuelSession(Base):
    __tablename__ = 'refuel_sessions'
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    vehicle = relationship("Vehicle")

    date = Column(DateTime)
    startSOC_pct = Column(Integer)
    endSOC_pct = Column(Integer)
    mileage_km = Column(Integer)
    # To be added Location

    def __init__(self, vehicle, date, startSOC_pct, endSOC_pct, mileage_km):
        self.vehicle = vehicle
        self.date = date
        self.startSOC_pct = startSOC_pct
        self.endSOC_pct = endSOC_pct
        self.mileage_km = mileage_km
