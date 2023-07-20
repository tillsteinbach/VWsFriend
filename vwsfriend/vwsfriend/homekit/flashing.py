import logging
from threading import Timer

import pyhap

from weconnect.errors import SetterError

from vwsfriend.homekit.genericAccessory import GenericAccessory

LOG = logging.getLogger("VWsFriend")


class Flashing(GenericAccessory):
    """Flashing Accessory"""

    category = pyhap.const.CATEGORY_LIGHTBULB

    def __init__(self, driver, bridge, aid, id, vin, displayName, flashControl):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.flashControl = flashControl
        self.service = self.add_preload_service('Lightbulb', ['Name', 'ConfiguredName', 'On'])

        self.charOn = self.service.configure_char('On', setter_callback=self.__onOnChanged)

        self.addNameCharacteristics()

    def __onOnChanged(self, value):
        if self.flashControl is not None and self.flashControl.enabled:
            try:
                if value is True:
                    LOG.info('Start flashing for 10 seconds')
                    self.flashControl.value = 10

                    def resetState():
                        self.charOn.set_value(False)

                    timer = Timer(10.0, resetState)
                    timer.start()
                else:
                    LOG.error('Flashing cannot be turned off, please wait for 10 seconds')
            except SetterError as setterError:
                LOG.error('Error flashing: %s', setterError)
                self.charOn.set_value(False)
                self.setStatusFault(1, timeout=120)
        else:
            LOG.error('Flashing cannot be controlled')
            self.charOn.set_value(False)
            self.setStatusFault(1, timeout=120)
