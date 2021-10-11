from sqlalchemy import Column, Integer, Float

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator


class WeConnectResponsetime(Base):
    __tablename__ = 'weconnect_responsetime'
    id = Column(Integer, primary_key=True)
    datetime = Column(DatetimeDecorator(timezone=True), nullable=False)
    min = Column(Float)
    avg = Column(Float)
    max = Column(Float)
    total = Column(Float)

    def __init__(self, datetime, min, avg, max, total):
        self.datetime = datetime
        self.min = min
        self.avg = avg
        self.max = max
        self.total = total
