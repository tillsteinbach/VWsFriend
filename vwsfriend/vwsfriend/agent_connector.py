import os
import time
import subprocess  # nosec
import logging

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from weconnect.elements import vehicle
from weconnect.addressable import AddressableLeaf
from weconnect.elements.range_status import RangeStatus

from vwsfriend.agents.range_agent import RangeAgent
from vwsfriend.agents.battery_agent import BatteryAgent
from vwsfriend.agents.charge_agent import ChargeAgent
from vwsfriend.agents.state_agent import StateAgent
from vwsfriend.agents.climatization_agent import ClimatizationAgent
from vwsfriend.agents.refuel_agent import RefuelAgent
from vwsfriend.agents.trip_agent import TripAgent
from vwsfriend.agents.weconnect_error_agent import WeconnectErrorAgent
from vwsfriend.agents.abrp.abrp_agent import ABRPAgent
from vwsfriend.model.base import Base
from vwsfriend.model import Vehicle

from vwsfriend.model.migrations import run_database_migrations

LOG = logging.getLogger("VWsFriend")


class AgentConnector():
    def __init__(self, weConnect, dbUrl, interval, withDB=False, withABRP=False, configDir='./', privacy=None):  # noqa: C901
        self.agents = {}

        if withDB:
            if os.path.isfile(configDir + '/provisioning/database.vwsfrienddbbackup'):
                try:
                    with open(configDir + '/provisioning/database.vwsfrienddbbackup', mode='rb') as file:
                        LOG.info('Trying to restore database backup')
                        process = subprocess.run(['pg_restore', '--clean', '--if-exists', '--format', 'c', '--dbname', dbUrl], stdin=file,  # nosec
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                        if process.returncode != 0:
                            LOG.error('pg_restore returned %d: %s', process.returncode, process.stderr.decode('ascii'))
                        else:
                            LOG.info('It looks like the backup could be successfully restored')
                finally:
                    os.remove(configDir + '/provisioning/database.vwsfrienddbbackup')

            engine = create_engine(dbUrl, pool_pre_ping=True)
            self.session = Session(engine)

            while True:
                try:
                    self.session.query(text('1')).from_statement(text('SELECT 1')).all()
                except OperationalError as err:
                    LOG.error('Could not establish a connection to database, will try again after 10 seconds: %s', err)
                    time.sleep(10)
                    continue
                break

            if not inspect(engine).has_table("vehicles"):
                LOG.info('It looks like you have an empty database will create all tables')
                Base.metadata.create_all(engine)
                run_database_migrations(dsn=dbUrl, stampOnly=True)
            else:
                LOG.info('It looks like you have an existing database will check if an upgrade is necessary')
                run_database_migrations(dsn=dbUrl)
                LOG.info('Database upgrade done')

            self.vehicles = self.session.query(Vehicle).all()
        self.withDB = withDB

        self.withABRP = withABRP

        self.interval = interval
        self.configDir = configDir

        if privacy is None:
            self.privacy = []
        else:
            self.privacy = privacy

        weConnect.addObserver(self.onEnable, AddressableLeaf.ObserverEvent.ENABLED, onUpdateComplete=True)

        self.agents["none"] = []
        if self.withDB:
            self.agents["none"].append(WeconnectErrorAgent(self.session, weConnect))

    def onEnable(self, element, flags):
        if (flags & AddressableLeaf.ObserverEvent.ENABLED) and isinstance(element, vehicle.Vehicle):
            if element.vin not in self.agents:
                self.agents[element.vin.value] = []
            if self.withDB:
                foundVehicle = None
                for dbVehicle in self.vehicles:
                    if dbVehicle.vin == element.vin.value:
                        LOG.info('Found matching vehicle for vin %s in database', element.vin.value)
                        foundVehicle = dbVehicle
                        break
                if foundVehicle is None:
                    LOG.info('Found no matching vehicle for vin %s in database, will create a new one', element.vin.value)
                    foundVehicle = Vehicle(element.vin.value)
                    self.session.add(foundVehicle)
                    self.session.commit()
                foundVehicle.connect(element)

                self.agents[element.vin.value].append(RangeAgent(self.session, foundVehicle))
                self.agents[element.vin.value].append(BatteryAgent(self.session, foundVehicle))
                self.agents[element.vin.value].append(ChargeAgent(self.session, foundVehicle, privacy=self.privacy))
                self.agents[element.vin.value].append(StateAgent(self.session, foundVehicle, updateInterval=self.interval))
                self.agents[element.vin.value].append(ClimatizationAgent(self.session, foundVehicle))
                self.agents[element.vin.value].append(RefuelAgent(self.session, foundVehicle, privacy=self.privacy))
                self.agents[element.vin.value].append(TripAgent(self.session, foundVehicle, updateInterval=self.interval, privacy=self.privacy))
                if foundVehicle.carType == RangeStatus.CarType.UNKNOWN:
                    LOG.warning('Vehicle %s has an unkown carType, thus some features won\'t be available until the correct carType could be detected',
                                foundVehicle.vin)
            if self.withABRP:
                self.agents[element.vin.value].append(ABRPAgent(weConnectVehicle=element, tokenfile=f'{self.configDir}/{element.vin.value}-ABRP.token'))

    def commit(self):
        for vehicleAgents in self.agents.values():
            for agent in vehicleAgents:
                agent.commit()
        if self.withDB:
            self.session.commit()
