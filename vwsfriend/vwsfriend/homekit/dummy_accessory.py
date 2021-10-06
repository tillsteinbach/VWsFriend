import logging

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_OTHER

LOG = logging.getLogger("VWsFriend")


class DummyAccessory(Accessory):

    category = CATEGORY_OTHER

    def __init__(self, driver, aid, displayName):
        super().__init__(driver=driver, display_name=displayName, aid=aid)

    @Accessory.available.getter
    def available(self):
        return False
