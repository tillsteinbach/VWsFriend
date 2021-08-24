import logging
import json
import pyhap

from .climatization import Climatization
from .battery import Battery
from .charging import Charging

from vwsfriend.__version import __version__

LOG = logging.getLogger("VWsFriend")


class VWsFriendBridge(pyhap.accessory.Bridge):
    """VWsfriend Bridge"""

    def __init__(self, weConnect, driver, displayName='VWsFriend', aidfile=None):
        super().__init__(driver=driver, display_name=displayName, )

        self.set_info_service(__version__, "Till Steinbach", "VWsFriend", None)

        self.weConnect = weConnect
        self.driver = driver

        self.aidfile = aidfile
        self.__aid = {}
        self.nextAID = 100
        try:
            self.readAIDs(aidfile)
        except FileNotFoundError:
            pass

    def persistAIDs(self, aidfile):
        if aidfile:
            try:
                with open(aidfile, 'w') as file:
                    json.dump(self.__aid, fp=file)
                LOG.info('Writing aidfile %s', aidfile)
            except ValueError as err:  # pragma: no cover
                LOG.info('Could not write homekit aidfile %s (%s)', aidfile, err)

    def readAIDs(self, aidfile):
        with open(aidfile, 'r') as file:
            aid = json.load(fp=file)
            self.__aid = aid
        LOG.info('Reading homekit aidfile %s', aidfile)
        for aid in self.__aid.values():
            if aid > self.nextAID:
                self.nextAID = aid

    def update(self):
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
                climatizationAccessory = Climatization(driver=self.driver, aid=self.selectAID('Climatization', vin), displayName=f'{nickname} Climatization',
                                                       climatizationStatus=climatizationStatus,
                                                       climatizationSettings=climatizationSettings)
                climatizationAccessory.set_info_service(manufacturer=manufacturer,
                                                        model=model,
                                                        serial_number=vin)
                self.add_accessory(climatizationAccessory)
                configChanged = True

            if 'batteryStatus' in vehicle.statuses:
                batteryStatus = vehicle.statuses['batteryStatus']

                if 'chargingStatus' in vehicle.statuses:
                    chargingStatus = vehicle.statuses['chargingStatus']
                else:
                    chargingStatus = None

                batteryAccessory = Battery(driver=self.driver, aid=self.selectAID('Battery', vin), displayName=f'{nickname} Battery',
                                           batteryStatus=batteryStatus,
                                           chargingStatus=chargingStatus)
                batteryAccessory.set_info_service(manufacturer=manufacturer,
                                                  model=model,
                                                  serial_number=vin)
                self.add_accessory(batteryAccessory)
                configChanged = True

            if 'chargingStatus' in vehicle.statuses:
                chargingStatus = vehicle.statuses['chargingStatus']

                if 'plugStatus' in vehicle.statuses:
                    plugStatus = vehicle.statuses['plugStatus']
                else:
                    plugStatus = None

                chargingAccessory = Charging(driver=self.driver, aid=self.selectAID('Charging', vin), displayName=f'{nickname} Charging',
                                             chargingStatus=chargingStatus,
                                             plugStatus=plugStatus)
                chargingAccessory.set_info_service(manufacturer=manufacturer,
                                                   model=model,
                                                   serial_number=vin)
                self.add_accessory(chargingAccessory)
                configChanged = True
        if configChanged:
            self.driver.config_changed()
            self.persistAIDs(self.aidfile)

    def selectAID(self, id, vin):
        aid = None
        identifier = f'{vin}-{id}'
        if identifier in self.__aid:
            aid = self.__aid[identifier]
        else:
            aid = self.nextAID
            self.__aid[identifier] = aid
            self.nextAID += 1
        return aid

