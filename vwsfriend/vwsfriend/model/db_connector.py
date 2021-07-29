from vwsfriend.agents.range_agent import RangeAgent
import weconnect
from weconnect.elements import vehicle

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vwsfriend.model.base import Base

from weconnect.addressable import AddressableLeaf
import weconnect.elements

from vwsfriend.model.vehicle import Vehicle



class DBConnector():
    def __init__(self, weConnect, dbUrl):

        engine = create_engine(dbUrl)
        self.session = Session(engine)

        Base.metadata.create_all(engine)

        self.vehicles = self.session.query(Vehicle).all()
        self.agents = list()

        weConnect.addObserver(self.onEnable, AddressableLeaf.ObserverEvent.ENABLED, onUpdateComplete=True)

    def onEnable(self, element, flags):
        if (flags & AddressableLeaf.ObserverEvent.ENABLED) and isinstance(element, vehicle.Vehicle):
            foundVehicle = None
            for dbVehicle in self.vehicles:
                if dbVehicle.vin == element.vin.value:
                    print('found')
                    foundVehicle = dbVehicle
                    break
            if foundVehicle is None:
                foundVehicle = Vehicle(element.vin.value)
                self.session.add(foundVehicle)
            foundVehicle.connect(element)
            self.agents.append(RangeAgent(self.session, foundVehicle))

    def commit(self):
        for agent in self.agents:
            agent.commit()
        self.session.commit()
