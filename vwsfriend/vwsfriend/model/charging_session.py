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
    charger_id = Column(String, ForeignKey('chargers.id'))
    charger = relationship("Charger")

    def __init__(self, vehicle):
        self.vehicle = vehicle

    def isConnectedState(self):
        return self.connected is not None and self.disconnected is None

    def isLockedState(self):
        return self.locked is not None and self.unlocked is None

    def isChargingState(self):
        return self.started is not None and self.ended is None

    def isClosed(self):
        return self.ended is not None or self.unlocked is not None or self.disconnected is not None

    def wasStarted(self):
        return self.started is not None

    def wasConnected(self):
        return self.connected is not None

    def wasLocked(self):
        return self.locked is not None

    def wasEnded(self):
        return self.ended is not None

    def wasDisconnected(self):
        return self.disconnected is not None

    def wasUnlocked(self):
        return self.unlocked is not None
