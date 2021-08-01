import logging

from vwsfriend.agents.range_agent import RangeAgent
from vwsfriend.agents.charge_agent import ChargeAgent
from vwsfriend.agents.state_agent import StateAgent
from vwsfriend.agents.climatization_agent import ClimatizationAgent
from weconnect.elements import vehicle

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vwsfriend.model.base import Base

from weconnect.addressable import AddressableLeaf

from vwsfriend.model.vehicle import Vehicle


LOG = logging.getLogger("VWsFriend")


class DBConnector():
    def __init__(self, weConnect, dbUrl, interval):

        engine = create_engine(dbUrl)
        self.session = Session(engine)

        Base.metadata.create_all(engine)

        self.vehicles = self.session.query(Vehicle).all()
        self.agents = list()

        self.interval = interval

        weConnect.addObserver(self.onEnable, AddressableLeaf.ObserverEvent.ENABLED, onUpdateComplete=True)

    def onEnable(self, element, flags):
        if (flags & AddressableLeaf.ObserverEvent.ENABLED) and isinstance(element, vehicle.Vehicle):
            foundVehicle = None
            for dbVehicle in self.vehicles:
                if dbVehicle.vin == element.vin.value:
                    LOG.info(f'Found matching vehicle for vin {element.vin.value} in database')
                    foundVehicle = dbVehicle
                    break
            if foundVehicle is None:
                LOG.info(f'Found no matching vehicle for vin {element.vin.value} in database, will create a new one')
                foundVehicle = Vehicle(element.vin.value)
                self.session.add(foundVehicle)
            foundVehicle.connect(element)
            self.agents.append(RangeAgent(self.session, foundVehicle))
            self.agents.append(ChargeAgent(self.session, foundVehicle))
            self.agents.append(StateAgent(self.session, foundVehicle, updateInterval=self.interval))
            self.agents.append(ClimatizationAgent(self.session, foundVehicle))

    def commit(self):
        for agent in self.agents:
            agent.commit()
        self.session.commit()
