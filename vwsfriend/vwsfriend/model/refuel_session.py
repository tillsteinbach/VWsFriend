from sqlalchemy import Column, Integer, BigInteger, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class RefuelSession(Base):
    __tablename__ = 'refuel_sessions'
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    vehicle = relationship("Vehicle")

    date = Column(DatetimeDecorator)
    startSOC_pct = Column(Integer)
    endSOC_pct = Column(Integer)
    mileage_km = Column(Integer)
    position_latitude = Column(Float)
    position_longitude = Column(Float)
    location_id = Column(BigInteger, ForeignKey('locations.osm_id'))
    location = relationship("Location")

    def __init__(self, vehicle, date, startSOC_pct, endSOC_pct, mileage_km, position_latitude, position_longitude, location):
        self.vehicle = vehicle
        self.date = date
        self.startSOC_pct = startSOC_pct
        self.endSOC_pct = endSOC_pct
        self.mileage_km = mileage_km
        self.position_latitude = position_latitude
        self.position_longitude = position_longitude
        self.location = location
