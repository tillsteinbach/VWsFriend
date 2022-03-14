import enum

from sqlalchemy import Column, Integer, String, Enum

from vwsfriend.model.base import Base


class UnitOfLength(enum.Enum):
    KM = 'km'
    MI = 'mi'


class UnitOfTemperature(enum.Enum):
    C = 'C'
    F = 'F'


class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    unit_of_length = Column(Enum(UnitOfLength))
    unit_of_temperature = Column(Enum(UnitOfTemperature))
    grafana_url = Column(String)
    vwsfriend_url = Column(String)
    locale = Column(String)

    def __init__(self, grafana_url, vwsfriend_url):
        self.unit_of_length = UnitOfLength.KM
        self.unit_of_temperature = UnitOfTemperature.C
        self.grafana_url = grafana_url
        self.vwsfriend_url = vwsfriend_url
        self.locale = 'en_US'
