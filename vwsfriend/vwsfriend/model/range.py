from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class Range(Base):
    __tablename__ = 'ranges'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'carCapturedTimestamp'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    carCapturedTimestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    vehicle = relationship("Vehicle")
    totalRange_km = Column(Integer)
    primary_currentSOC_pct = Column(Integer)
    primary_remainingRange_km = Column(Integer)
    secondary_currentSOC_pct = Column(Integer)
    secondary_remainingRange_km = Column(Integer)

    def __init__(self, vehicle, carCapturedTimestamp, totalRange_km, primary_currentSOC_pct, primary_remainingRange_km, secondary_currentSOC_pct,
                 secondary_remainingRange_km):
        self.vehicle = vehicle
        self.carCapturedTimestamp = carCapturedTimestamp
        self.totalRange_km = totalRange_km
        self.primary_currentSOC_pct = primary_currentSOC_pct
        self.primary_remainingRange_km = primary_remainingRange_km
        self.secondary_currentSOC_pct = secondary_currentSOC_pct
        self.secondary_remainingRange_km = secondary_remainingRange_km
