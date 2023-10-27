from sqlalchemy import Column, Integer, Float, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class BatteryTemperature(Base):
    __tablename__ = 'battery_temperature'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'carCapturedTimestamp'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    carCapturedTimestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    vehicle = relationship("Vehicle")
    temperatureHvBatteryMin_K = Column(Float)
    temperatureHvBatteryMax_K = Column(Float)

    def __init__(self, vehicle, carCapturedTimestamp, temperatureHvBatteryMin_K, temperatureHvBatteryMax_K):
        self.vehicle = vehicle
        self.carCapturedTimestamp = carCapturedTimestamp
        self.temperatureHvBatteryMin_K = temperatureHvBatteryMin_K
        self.temperatureHvBatteryMax_K = temperatureHvBatteryMax_K
