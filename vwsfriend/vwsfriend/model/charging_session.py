import enum

from sqlalchemy import Column, Integer, BigInteger, Float, String, DateTime, Enum, ForeignKey
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
    maximumChargePower_kW = Column(Integer)
    acdc = Column(Enum(ACDC, length=63))
    startSOC_pct = Column(Integer)
    endSOC_pct = Column(Integer)
    mileage_km = Column(Integer)
    position_latitude = Column(Float)
    position_longitude = Column(Float)
    location_id = Column(BigInteger, ForeignKey('locations.osm_id'))
    location = relationship("Location")

    def __init__(self, vehicle):
        self.vehicle = vehicle
