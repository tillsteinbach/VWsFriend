from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from weconnect.elements.warning_lights_status import WarningLightsStatus

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class WarningLight(Base):
    __tablename__ = 'warning_lights'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'messageId', 'start'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    start = Column(DatetimeDecorator(timezone=True), nullable=False)
    start_mileage = Column(Integer)
    end = Column(DatetimeDecorator(timezone=True))
    end_mileage = Column(Integer)
    vehicle = relationship("Vehicle")
    text = Column(String)
    category = Column(Enum(WarningLightsStatus.WarningLight.Category))
    messageId = Column(String)
    priority = Column(Integer)
    serviceLead = Column(Boolean)
    customerRelevance = Column(Boolean)

    def __init__(self, vehicle, messageId, start, text, category):
        self.vehicle = vehicle
        self.messageId = messageId
        self.start = start
        self.text = text
        self.category = category
