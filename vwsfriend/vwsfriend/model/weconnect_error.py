from sqlalchemy import Column, Integer, String, Enum

from vwsfriend.model.base import Base
from vwsfriend.model.datetime_decorator import DatetimeDecorator

from weconnect.weconnect import WeConnect


class WeConnectError(Base):
    __tablename__ = 'weconnect_errors'
    id = Column(Integer, primary_key=True)
    datetime = Column(DatetimeDecorator(timezone=True), nullable=False)
    errortype = Column(Enum(WeConnect.ErrorEventType, length=63))
    detail = Column(String)

    def __init__(self, datetime, errortype, detail):
        self.datetime = datetime
        self.errortype = errortype
        self.detail = detail
