from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base


class Charger(Base):
    __tablename__ = 'chargers'
    id = Column(String, primary_key=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    max_power = Column(Float)
    num_spots = Column(Integer)
    operator_id = Column(String, ForeignKey('operators.id'))
    operator = relationship("Operator")
    custom = Column(Boolean)

    def __init__(self, id, custom=False):
        self.id = id
        self.custom = custom


class Operator(Base):
    __tablename__ = 'operators'
    id = Column(String, primary_key=True)
    name = Column(String)
    phone = Column(String)
    custom = Column(Boolean)

    def __init__(self, id, name, phone, custom=False):
        self.id = id
        self.name = name
        self.phone = phone
        self.custom = custom

    def displayString(self):
        return self.name
