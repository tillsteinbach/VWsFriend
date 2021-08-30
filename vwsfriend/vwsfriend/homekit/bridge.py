import logging
import json
import pyhap

from weconnect.weconnect import WeConnect

from .climatization import Climatization
# from .battery import Battery
from .charging import Charging
from .plug import Plug
from .locking_system import LockingSystem

from vwsfriend.__version import __version__

LOG = logging.getLogger("VWsFriend")


class VWsFriendBridge(pyhap.accessory.Bridge):
    """VWsfriend Bridge"""

    def __init__(self, weConnect: WeConnect, driver, displayName='VWsFriend', accessoryConfigFile=None):
        super().__init__(driver=driver, display_name=displayName, )

        self.set_info_service(__version__, "Till Steinbach", "VWsFriend", None)

        self.weConnect: WeConnect = weConnect
        self.driver = driver

        self.accessoryConfigFile = accessoryConfigFile
        self.__accessoryConfig = {}
        self.nextAID = 100
        try:
            self.readConfig()
        except FileNotFoundError:
            pass

    def persistConfig(self):
        if self.accessoryConfigFile:
            try:
                with open(self.accessoryConfigFile, 'w') as file:
                    json.dump(self.__accessoryConfig, fp=file)
                LOG.info('Writing accessory config file %s', self.accessoryConfigFile)
            except ValueError as err:  # pragma: no cover
                LOG.info('Could not write homekit accessoryConfigFile %s (%s)', self.accessoryConfigFile, err)

    def readConfig(self):
        with open(self.accessoryConfigFile, 'r') as file:
            aid = json.load(fp=file)
            self.__accessoryConfig = aid
        LOG.info('Reading homekit accessory config file %s', self.accessoryConfigFile)
        for accessoryConfig in self.__accessoryConfig.values():
            if 'aid' in accessoryConfig:
                if (accessoryConfig['aid'] + 1) > self.nextAID:
                    self.nextAID = (accessoryConfig['aid'] + 1)

    def update(self):  # noqa: C901
        configChanged = False
        for vehicle in self.weConnect.vehicles.values():
            manufacturer = 'Volkswagen'
            nickname = vehicle.nickname.value
            model = vehicle.nickname.value
            vin = vehicle.vin.value
            # Climatization
            if 'climatisationStatus' in vehicle.statuses:
                climatizationStatus = vehicle.statuses['climatisationStatus']

                if 'climatisationSettings' in vehicle.statuses:
                    climatizationSettings = vehicle.statuses['climatisationSettings']
                else:
                    climatizationSettings = None

                if 'batteryStatus' in vehicle.statuses:
                    batteryStatus = vehicle.statuses['batteryStatus']
                else:
                    batteryStatus = None

                if 'chargingStatus' in vehicle.statuses:
                    chargingStatus = vehicle.statuses['chargingStatus']
                else:
                    chargingStatus = None

                climatizationAccessory = Climatization(driver=self.driver, bridge=self, aid=self.selectAID('Climatization', vin), id='Climatization', vin=vin,
                                                       displayName=f'{nickname} Climatization', climatizationStatus=climatizationStatus,
                                                       climatizationSettings=climatizationSettings, batteryStatus=batteryStatus, chargingStatus=chargingStatus,
                                                       climatizationControl=vehicle.controls.climatizationControl)
                climatizationAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-climatization')
                self.add_accessory(climatizationAccessory)
                configChanged = True

            # if 'batteryStatus' in vehicle.statuses:
            #     batteryStatus = vehicle.statuses['batteryStatus']

            #     if 'chargingStatus' in vehicle.statuses:
            #         chargingStatus = vehicle.statuses['chargingStatus']
            #     else:
            #         chargingStatus = None

            #     batteryAccessory = Battery(driver=self.driver, bridge=self, aid=self.selectAID('Battery', vin), id='Battery', vin=vin,
            #                                displayName=f'{nickname} Battery', batteryStatus=batteryStatus, chargingStatus=chargingStatus)
            #     batteryAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-battery')
            #     self.add_accessory(batteryAccessory)
            #     configChanged = True

            if 'chargingStatus' in vehicle.statuses:
                chargingStatus = vehicle.statuses['chargingStatus']

                if 'plugStatus' in vehicle.statuses:
                    plugStatus = vehicle.statuses['plugStatus']
                else:
                    plugStatus = None

                if 'batteryStatus' in vehicle.statuses:
                    batteryStatus = vehicle.statuses['batteryStatus']
                else:
                    batteryStatus = None

                chargingAccessory = Charging(driver=self.driver, bridge=self, aid=self.selectAID('Charging', vin), id='Charging', vin=vin,
                                             displayName=f'{nickname} Charging', chargingStatus=chargingStatus, plugStatus=plugStatus,
                                             batteryStatus=batteryStatus, chargingControl=vehicle.controls.chargingControl)
                chargingAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-charging')
                self.add_accessory(chargingAccessory)
                configChanged = True

            if 'plugStatus' in vehicle.statuses:
                plugStatus = vehicle.statuses['plugStatus']

                plugAccessory = Plug(driver=self.driver, bridge=self, aid=self.selectAID('ChargingPlug', vin), id='ChargingPlug', vin=vin,
                                     displayName=f'{nickname} Charging Plug', plugStatus=plugStatus)
                plugAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-charging_plug')
                self.add_accessory(plugAccessory)
                configChanged = True

            if 'accessStatus' in vehicle.statuses:
                accessStatus = vehicle.statuses['accessStatus']

                lockingSystemAccessory = LockingSystem(driver=self.driver, bridge=self, aid=self.selectAID('LockingSystem', vin), id='LockingSystem', vin=vin,
                                                       displayName=f'{nickname} Locking System', accessStatus=accessStatus)
                lockingSystemAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-locking_system')
                self.add_accessory(lockingSystemAccessory)
                configChanged = True

        if configChanged:
            self.driver.config_changed()
            self.persistConfig()

    def selectAID(self, id, vin):
        aid = None
        identifier = f'{vin}-{id}'
        if identifier in self.__accessoryConfig and 'aid' in self.__accessoryConfig[identifier]:
            aid = self.__accessoryConfig[identifier]['aid']
        else:
            aid = self.nextAID
            self.nextAID += 1
            if identifier in self.__accessoryConfig:
                self.__accessoryConfig[identifier]['aid'] = aid
            else:
                self.__accessoryConfig[identifier] = {'aid': aid}
        return aid

    def setConfigItem(self, id, vin, configKey, item):
        identifier = f'{vin}-{id}'
        if identifier in self.__accessoryConfig:
            self.__accessoryConfig[identifier][configKey] = item
        else:
            self.__accessoryConfig[identifier] = {configKey: item}
        self.nextAID += 1

    def getConfigItem(self, id, vin, configKey):
        identifier = f'{vin}-{id}'
        if identifier in self.__accessoryConfig and configKey in self.__accessoryConfig[identifier]:
            return self.__accessoryConfig[identifier][configKey]
        return None
