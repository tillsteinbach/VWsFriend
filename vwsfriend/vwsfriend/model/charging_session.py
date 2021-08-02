import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base

from weconnect.elements.charging_settings import ChargingSettings


class ACDC(enum.Enum,):
    AC = enum.auto()
    DC = enum.auto()
    UNKNOWN = enum.auto()


class ChargingSession(Base):
    __tablename__ = 'charging_sessions'
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    vehicle = relationship("Vehicle")

    connected = Column(DateTime)
    locked = Column(DateTime)
    started = Column(DateTime)
    ended = Column(DateTime)
    unlocked = Column(DateTime)
    disconnected = Column(DateTime)
    maxChargeCurrentACSetting = Column(Enum(ChargingSettings.MaximumChargeCurrent, length=63))
    targetSOCSetting_pct = Column(Integer)
    targetSOCSetting_pct = Column(Integer)
    maximumChargePower_kW = Column(Integer)
    averageChargePower_kW = Column(Integer)
    maximumChargeRate_kmph = Column(Integer)
    acdc = Column(Enum(ACDC, length=63))
    startSOC_pct = Column(Integer)
    endSOC_pct = Column(Integer)
    mileage_km = Column(Integer)
    cost = Column(Integer)
    # To be added Location
    # To be added Charger

    def __init__(self, vehicle):
        self.vehicle = vehicle
