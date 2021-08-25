import logging

import pyhap

LOG = logging.getLogger("VWsFriend")


class GenericAccessory(pyhap.accessory.Accessory):
    def __init__(self, driver, bridge, aid, id, vin, displayName):
        super().__init__(driver=driver, display_name=displayName, aid=aid)

        self.driver = driver
        self.bridge = bridge
        self.aid = aid
        self.id = id
        self.vin = vin
        self.displayName = displayName

        self.service = None

    def addNameCharacteristics(self):
        configuredName = self.bridge.getConfigItem(self.id, self.vin, 'ConfiguredName')
        if configuredName is None:
            configuredName = self.displayName
        if self.service is not None:
            self.charConfiguredName = self.service.configure_char('ConfiguredName', value=configuredName, setter_callback=self.__onConfiguredNameChanged)
            self.charName = self.service.configure_char('Name', value=configuredName)

    def __onConfiguredNameChanged(self, value):
        if value is not None and len(value) > 0:
            self.bridge.setConfigItem(self.id, self.vin, 'ConfiguredName', value)
            self.bridge.persistConfig()
            self.charConfiguredName.set_value(value)
            self.charName.set_value(value)
