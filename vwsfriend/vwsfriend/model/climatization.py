from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator

from weconnect.elements.climatization_status import ClimatizationStatus


class Climatization(Base):
    __tablename__ = 'climatization'
    __table_args__ = (
        UniqueConstraint('vehicle_vin', 'carCapturedTimestamp'),
    )
    id = Column(Integer, primary_key=True)
    vehicle_vin = Column(String, ForeignKey('vehicles.vin'))
    carCapturedTimestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    vehicle = relationship("Vehicle")
    remainingClimatisationTime_min = Column(Integer)
    climatisationState = Column(Enum(ClimatizationStatus.ClimatizationState))

    def __init__(self, vehicle, carCapturedTimestamp, remainingClimatisationTime_min, climatisationState):
        self.vehicle = vehicle
        self.carCapturedTimestamp = carCapturedTimestamp
        self.remainingClimatisationTime_min = remainingClimatisationTime_min
        self.climatisationState = climatisationState
