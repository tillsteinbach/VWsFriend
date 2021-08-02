from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base

from weconnect.elements.charging_status import ChargingStatus


class Location(Base):
    __tablename__ = 'locations'
    osm_id = Column(Integer, primary_key=True)
    osm_type = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    display_name = Column(String)
    amenity = Column(String)
    house_number = Column(String)
    road = Column(String)
    suburb = Column(String)
    city = Column(String)
    postcode = Column(String)
    county = Column(String)
    country = Column(String)
    state = Column(String)
    state_district = Column(String)
    neighbourhood = Column(String)
    raw = Column(String)

    def __init__(self, jsonDict):
        pass

