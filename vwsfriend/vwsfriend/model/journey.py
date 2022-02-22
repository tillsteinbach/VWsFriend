from sqlalchemy import Column, Integer, String, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship, backref

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


journey_tag_association_table = Table('journey_tag', Base.metadata,
                                      Column('journey_id', ForeignKey('journey.id')),
                                      Column('tag_name', ForeignKey('tag.name'))
                                      )


class Journey(Base):
    __tablename__ = 'journey'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'start'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    start = Column(DatetimeDecorator(timezone=True), nullable=False)
    end = Column(DatetimeDecorator(timezone=True), nullable=False)
    vehicle = relationship("Vehicle")
    title = Column(String)
    description = Column(String)
    tags = relationship("Tag", secondary=journey_tag_association_table, backref=backref("journey"))

    def __init__(self, vehicle, start, end, title):
        self.vehicle = vehicle
        self.start = start
        self.end = end
        self.title = title
