import logging

import pyhap

from weconnect.addressable import AddressableLeaf
from weconnect.elements.plug_status import PlugStatus

from vwsfriend.homekit.genericAccessory import GenericAccessory

LOG = logging.getLogger("VWsFriend")


class Plug(GenericAccessory):
    """Plug Accessory"""

    category = pyhap.const.CATEGORY_SENSOR

    def __init__(self, driver, bridge, aid, id, vin, displayName, plugStatus):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.service = self.add_preload_service('ContactSensor', ['Name', 'ConfiguredName', 'ContactSensorState', 'StatusFault'])

        if plugStatus is not None and plugStatus.plugConnectionState.enabled:
            plugStatus.plugConnectionState.addObserver(self.onplugConnectionStateChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charContactSensorState = self.service.configure_char('ContactSensorState')
            self.charStatusFault = self.service.configure_char('StatusFault')
            self.setContactSensorState(plugStatus.plugConnectionState)

        self.addNameCharacteristics()

    def setContactSensorState(self, plugConnectionState):
        if self.charContactSensorState is not None:
            if plugConnectionState.value == PlugStatus.PlugConnectionState.CONNECTED:
                self.charContactSensorState.set_value(0)
                self.charStatusFault.set_value(0)
            elif plugConnectionState.value in (PlugStatus.PlugConnectionState.DISCONNECTED,
                                               PlugStatus.PlugConnectionState.UNSUPPORTED,
                                               PlugStatus.PlugConnectionState.INVALID):
                self.charContactSensorState.set_value(1)
                self.charStatusFault.set_value(0)
            else:
                self.charContactSensorState.set_value(0)
                self.charStatusFault.set_value(1)
                LOG.warn('unsupported plugConnectionState: %s', plugConnectionState.value.value)

    def onplugConnectionStateChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setContactSensorState(element)
            LOG.debug('Plug connection state Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)
