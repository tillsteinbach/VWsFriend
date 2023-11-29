import logging
import json
from vwsfriend.homekit.dummy_accessory import DummyAccessory
import pyhap

from weconnect.weconnect import WeConnect

from .climatization import Climatization
# from .battery import Battery
from .charging import Charging
from .plug import Plug
from .locking_system import LockingSystem
from .flashing import Flashing
from .battery_temperature import BatteryTemperature

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

        for identifier, accessory in self.__accessoryConfig.items():
            if 'ConfiguredName' in accessory:
                displayName = accessory['ConfiguredName']
            else:
                displayName = identifier
            placeholderAccessory = DummyAccessory(driver=driver, displayName=displayName, aid=accessory['aid'])
            if 'category' in accessory:
                placeholderAccessory.category = accessory['category']
            if 'services' in accessory:
                for service in accessory['services']:
                    placeholderAccessory.add_preload_service(service, chars=None)
            self.add_accessory(placeholderAccessory)

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
            if vehicle.statusExists('climatisation', 'climatisationStatus'):
                climatizationStatus = vehicle.domains['climatisation']['climatisationStatus']

                if vehicle.statusExists('climatisation', 'climatisationSettings'):
                    climatizationSettings = vehicle.domains['climatisation']['climatisationSettings']
                else:
                    climatizationSettings = None

                if vehicle.statusExists('charging', 'batteryStatus'):
                    batteryStatus = vehicle.domains['charging']['batteryStatus']
                else:
                    batteryStatus = None

                if vehicle.statusExists('charging', 'chargingStatus'):
                    chargingStatus = vehicle.domains['charging']['chargingStatus']
                else:
                    chargingStatus = None

                climatizationAccessory = Climatization(driver=self.driver, bridge=self, aid=self.selectAID('Climatization', vin), id='Climatization', vin=vin,
                                                       displayName=f'{nickname} Climatization', climatizationStatus=climatizationStatus,
                                                       climatizationSettings=climatizationSettings, batteryStatus=batteryStatus, chargingStatus=chargingStatus,
                                                       climatizationControl=vehicle.controls.climatizationControl)
                climatizationAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-climatization')
                self.setConfigItem(climatizationAccessory.id, climatizationAccessory.vin, 'category', climatizationAccessory.category)
                self.setConfigItem(climatizationAccessory.id, climatizationAccessory.vin, 'services',
                                   [service.display_name for service in climatizationAccessory.services])
                if climatizationAccessory.aid not in self.accessories:
                    self.add_accessory(climatizationAccessory)
                else:
                    self.accessories[climatizationAccessory.aid] = climatizationAccessory
                configChanged = True

            if vehicle.statusExists('charging', 'chargingStatus'):
                chargingStatus = vehicle.domains['charging']['chargingStatus']

                if vehicle.statusExists('charging', 'plugStatus'):
                    plugStatus = vehicle.domains['charging']['plugStatus']
                else:
                    plugStatus = None

                if vehicle.statusExists('charging', 'batteryStatus'):
                    batteryStatus = vehicle.domains['charging']['batteryStatus']
                else:
                    batteryStatus = None

                chargingAccessory = Charging(driver=self.driver, bridge=self, aid=self.selectAID('Charging', vin), id='Charging', vin=vin,
                                             displayName=f'{nickname} Charging', chargingStatus=chargingStatus, plugStatus=plugStatus,
                                             batteryStatus=batteryStatus, chargingControl=vehicle.controls.chargingControl)
                chargingAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-charging')
                self.setConfigItem(chargingAccessory.id, chargingAccessory.vin, 'category', chargingAccessory.category)
                self.setConfigItem(chargingAccessory.id, chargingAccessory.vin, 'services', [service.display_name for service in chargingAccessory.services])
                if chargingAccessory.aid not in self.accessories:
                    self.add_accessory(chargingAccessory)
                else:
                    self.accessories[chargingAccessory.aid] = chargingAccessory
                configChanged = True

            if vehicle.statusExists('charging', 'plugStatus'):
                plugStatus = vehicle.domains['charging']['plugStatus']

                plugAccessory = Plug(driver=self.driver, bridge=self, aid=self.selectAID('ChargingPlug', vin), id='ChargingPlug', vin=vin,
                                     displayName=f'{nickname} Charging Plug', plugStatus=plugStatus)
                plugAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-charging_plug')
                self.setConfigItem(plugAccessory.id, plugAccessory.vin, 'category', plugAccessory.category)
                self.setConfigItem(plugAccessory.id, plugAccessory.vin, 'services', [service.display_name for service in plugAccessory.services])
                if plugAccessory.aid not in self.accessories:
                    self.add_accessory(plugAccessory)
                else:
                    self.accessories[plugAccessory.aid] = plugAccessory
                configChanged = True

            if vehicle.statusExists('access', 'accessStatus') and vehicle.domains['access']['accessStatus'].carCapturedTimestamp.enabled:
                accessStatus = vehicle.domains['access']['accessStatus']

                if vehicle.controls.accessControl is not None and vehicle.controls.accessControl.enabled:
                    accessControl = vehicle.controls.accessControl
                else:
                    accessControl = None

                lockingSystemAccessory = LockingSystem(driver=self.driver, bridge=self, aid=self.selectAID('LockingSystem', vin), id='LockingSystem', vin=vin,
                                                       displayName=f'{nickname} Locking System', accessStatus=accessStatus, accessControl=accessControl)
                lockingSystemAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-locking_system')
                self.setConfigItem(lockingSystemAccessory.id, lockingSystemAccessory.vin, 'category', lockingSystemAccessory.category)
                self.setConfigItem(lockingSystemAccessory.id, lockingSystemAccessory.vin, 'services',
                                   [service.display_name for service in lockingSystemAccessory.services])
                if lockingSystemAccessory.aid not in self.accessories:
                    self.add_accessory(lockingSystemAccessory)
                else:
                    self.accessories[lockingSystemAccessory.aid] = lockingSystemAccessory
                configChanged = True

            if vehicle.controls.honkAndFlashControl is not None and vehicle.controls.honkAndFlashControl.enabled:
                honkAndFlashControl = vehicle.controls.honkAndFlashControl

                flashingAccessory = Flashing(driver=self.driver, bridge=self, aid=self.selectAID('Flashing', vin), id='Flashing', vin=vin,
                                             displayName=f'{nickname} Flashing', flashControl=honkAndFlashControl)
                flashingAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-flashing')
                self.setConfigItem(flashingAccessory.id, flashingAccessory.vin, 'category', flashingAccessory.category)
                self.setConfigItem(flashingAccessory.id, flashingAccessory.vin, 'services',
                                   [service.display_name for service in flashingAccessory.services])
                if flashingAccessory.aid not in self.accessories:
                    self.add_accessory(flashingAccessory)
                else:
                    self.accessories[flashingAccessory.aid] = flashingAccessory
                configChanged = True

            if vehicle.statusExists('measurements', 'temperatureBatteryStatus') \
                    and vehicle.domains['measurements']['temperatureBatteryStatus'].carCapturedTimestamp.enabled:
                temperatureBatteryStatus = vehicle.domains['measurements']['temperatureBatteryStatus']

                if vehicle.statusExists('charging', 'batteryStatus'):
                    batteryStatus = vehicle.domains['charging']['batteryStatus']

                    if vehicle.statusExists('charging', 'chargingStatus'):
                        chargingStatus = vehicle.domains['charging']['chargingStatus']
                    else:
                        chargingStatus = None

                    batteryTemperatureAccessory = BatteryTemperature(driver=self.driver, bridge=self, aid=self.selectAID('BatteryTemperature', vin),
                                                                     id='BatteryTemperature', vin=vin, displayName=f'{nickname} Battery Temperature',
                                                                     batteryStatus=batteryStatus, batteryTemperatureStatus=temperatureBatteryStatus,
                                                                     chargingStatus=chargingStatus)

                    batteryTemperatureAccessory.set_info_service(manufacturer=manufacturer, model=model, serial_number=f'{vin}-battery_termperature')
                    self.setConfigItem(batteryTemperatureAccessory.id, batteryTemperatureAccessory.vin, 'category', batteryTemperatureAccessory.category)
                    self.setConfigItem(batteryTemperatureAccessory.id, batteryTemperatureAccessory.vin, 'services',
                                       [service.display_name for service in batteryTemperatureAccessory.services])
                    if batteryTemperatureAccessory.aid not in self.accessories:
                        self.add_accessory(batteryTemperatureAccessory)
                    else:
                        self.accessories[batteryTemperatureAccessory.aid] = batteryTemperatureAccessory
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
