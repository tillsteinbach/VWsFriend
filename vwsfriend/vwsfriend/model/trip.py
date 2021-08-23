from sqlalchemy import Column, Integer, BigInteger, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    vehicle = relationship("Vehicle")

    startDate = Column(DatetimeDecorator)
    endDate = Column(DatetimeDecorator)
    start_position_latitude = Column(Float)
    start_position_longitude = Column(Float)
    start_location_id = Column(BigInteger, ForeignKey('locations.osm_id'))
    start_location = relationship("Location", foreign_keys=[start_location_id])
    destination_position_latitude = Column(Float)
    destination_position_longitude = Column(Float)
    destination_location_id = Column(BigInteger, ForeignKey('locations.osm_id'))
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    start_mileage_km = Column(Integer)
    end_mileage_km = Column(Integer)

    def __init__(self, vehicle, startDate, start_position_latitude, start_position_longitude, start_location, start_mileage_km):
        self.vehicle = vehicle
        self.startDate = startDate
        self.start_position_latitude = start_position_latitude
        self.start_position_longitude = start_position_longitude
        self.start_location = start_location
        self.start_mileage_km = start_mileage_km
