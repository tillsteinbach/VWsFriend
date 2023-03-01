import enum

from sqlalchemy import Column, Integer, BigInteger, Float, String, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship, backref

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator

from weconnect.elements.enums import MaximumChargeCurrent


class ACDC(enum.Enum,):
    AC = enum.auto()
    DC = enum.auto()
    UNKNOWN = enum.auto()

    def __str__(self):
        return self.name

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return item if isinstance(item, ACDC) else ACDC[item]


charging_tag_association_table = Table('charging_tag', Base.metadata,
                                       Column('charging_sessions_id', ForeignKey('charging_sessions.id')),
                                       Column('tag_name', ForeignKey('tag.name'))
                                       )


class ChargingSession(Base):
    __tablename__ = 'charging_sessions'
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    vehicle = relationship("Vehicle")

    connected = Column(DatetimeDecorator)
    locked = Column(DatetimeDecorator)
    started = Column(DatetimeDecorator)
    ended = Column(DatetimeDecorator)
    unlocked = Column(DatetimeDecorator)
    disconnected = Column(DatetimeDecorator)
    maxChargeCurrentACSetting = Column(Enum(MaximumChargeCurrent))
    targetSOCSetting_pct = Column(Integer)
    maximumChargePower_kW = Column(Float)
    acdc = Column(Enum(ACDC), index=True)
    startSOC_pct = Column(Integer)
    endSOC_pct = Column(Integer)
    mileage_km = Column(Integer)
    position_latitude = Column(Float)
    position_longitude = Column(Float)
    location_id = Column(BigInteger, ForeignKey('locations.osm_id'))
    location = relationship("Location")
    charger_id = Column(String, ForeignKey('chargers.id'))
    charger = relationship("Charger")
    meterStart_kWh = Column(Float)
    meterEnd_kWh = Column(Float)
    pricePerKwh_ct = Column(Float)
    pricePerMinute_ct = Column(Float)
    pricePerSession_ct = Column(Float)
    realCharged_kWh = Column(Float)
    realCost_ct = Column(Integer)
    tags = relationship("Tag", secondary=charging_tag_association_table, backref=backref("charging_sessions"))

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
