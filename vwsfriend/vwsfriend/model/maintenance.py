import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class MaintenanceType(enum.Enum,):
    INSPECTION = enum.auto()
    OIL_SERVICE = enum.auto()
    UNKNOWN = enum.auto()

    def __str__(self):
        return self.name

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return item if isinstance(item, MaintenanceType) else MaintenanceType[item]


class Maintenance(Base):
    __tablename__ = 'maintenance'
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    vehicle = relationship("Vehicle")
    date = Column(DatetimeDecorator(timezone=True))
    mileage = Column(Integer)
    type = Column(Enum(MaintenanceType))
    due_in_days = Column(Integer)
    due_in_km = Column(Integer)

    def __init__(self, vehicle, date, mileage, type, due_in_days, due_in_km):
        self.vehicle = vehicle
        self.date = date
        self.mileage = mileage
        self.type = type
        self.due_in_days = due_in_days
        self.due_in_km = due_in_km
