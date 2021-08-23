from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class Battery(Base):
    __tablename__ = 'battery'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'carCapturedTimestamp'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    carCapturedTimestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    vehicle = relationship("Vehicle")
    currentSOC_pct = Column(Integer)
    cruisingRangeElectric_km = Column(Integer)

    def __init__(self, vehicle, carCapturedTimestamp, currentSOC_pct, cruisingRangeElectric_km):
        self.vehicle = vehicle
        self.carCapturedTimestamp = carCapturedTimestamp
        self.currentSOC_pct = currentSOC_pct
        self.cruisingRangeElectric_km = cruisingRangeElectric_km
