import logging

import pyhap

from .climatization import Climatization
from .battery import Battery
from .charging import Charging

LOG = logging.getLogger("VWsFriend")


class VWsFriendBridge(pyhap.accessory.Bridge):
    """VWsfriend Bridge"""

    def __init__(self, weConnect, driver, displayName='VWsFriend'):
        super().__init__(driver=driver, display_name=displayName)

        self.weConnect = weConnect
        self.driver = driver

    def update(self):
        for vehicle in self.weConnect.vehicles.values():
            nickname = vehicle.nickname.value
            # Climatization
            if 'climatisationStatus' in vehicle.statuses:
                climatizationStatus = vehicle.statuses['climatisationStatus']

                if 'climatisationSettings' in vehicle.statuses:
                    climatizationSettings = vehicle.statuses['climatisationSettings']
                else:
                    climatizationSettings = None
                climatizationAccessory = Climatization(driver=self.driver, displayName=f'{nickname} Climatization',
                                                       climatizationStatus=climatizationStatus,
                                                       climatizationSettings=climatizationSettings)
                self.add_accessory(climatizationAccessory)

            if 'batteryStatus' in vehicle.statuses:
                batteryStatus = vehicle.statuses['batteryStatus']

                if 'chargingStatus' in vehicle.statuses:
                    chargingStatus = vehicle.statuses['chargingStatus']
                else:
                    chargingStatus = None

                batteryAccessory = Battery(driver=self.driver, displayName=f'{nickname} Battery',
                                           batteryStatus=batteryStatus,
                                           chargingStatus=chargingStatus)
                self.add_accessory(batteryAccessory)

            if 'chargingStatus' in vehicle.statuses:
                chargingStatus = vehicle.statuses['chargingStatus']

                if 'plugStatus' in vehicle.statuses:
                    plugStatus = vehicle.statuses['plugStatus']
                else:
                    plugStatus = None

                chargingAccessory = Charging(driver=self.driver, displayName=f'{nickname} Charging',
                                             chargingStatus=chargingStatus,
                                             plugStatus=plugStatus)
                self.add_accessory(chargingAccessory)
