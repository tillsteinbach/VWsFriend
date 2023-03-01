from sqlalchemy import Column, Integer, Float, String, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator

from weconnect.elements.charging_status import ChargingStatus


class Charge(Base):
    __tablename__ = 'charges'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'carCapturedTimestamp'),
        Index("charges_idx_vehicle_vin_chargepower_kw", "vehicle_vin", "chargePower_kW"),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    carCapturedTimestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    vehicle = relationship("Vehicle")
    remainingChargingTimeToComplete_min = Column(Integer)
    chargingState = Column(Enum(ChargingStatus.ChargingState), index=True)
    chargeMode = Column(Enum(ChargingStatus.ChargeMode))
    chargePower_kW = Column(Float, index=True)
    chargeRate_kmph = Column(Float)

    def __init__(self, vehicle, carCapturedTimestamp, remainingChargingTimeToComplete_min, chargingState, chargeMode, chargePower_kW, chargeRate_kmph):
        self.vehicle = vehicle
        self.carCapturedTimestamp = carCapturedTimestamp
        self.remainingChargingTimeToComplete_min = remainingChargingTimeToComplete_min
        self.chargingState = chargingState
        self.chargeMode = chargeMode
        self.chargePower_kW = chargePower_kW
        self.chargeRate_kmph = chargeRate_kmph
