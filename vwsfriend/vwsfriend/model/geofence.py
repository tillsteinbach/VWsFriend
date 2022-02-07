from sqlalchemy import Column, String, Float, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base


class Geofence(Base):
    __tablename__ = 'geofences'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float)
    location_id = Column(BigInteger, ForeignKey('locations.osm_id'))
    location = relationship("Location")
    charger_id = Column(String, ForeignKey('chargers.id'))
    charger = relationship("Charger")

    def __init__(self, id):
        self.id = id
