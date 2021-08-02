import logging

import pyhap

from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.plug_status import PlugStatus
from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class Charging(pyhap.accessory.Accessory):
    """Charging Assessory"""

    category = pyhap.const.CATEGORY_OUTLET

    def __init__(self, driver, displayName, chargingStatus, plugStatus=None):
        super().__init__(driver=driver, display_name=displayName)

        servOutlet = self.add_preload_service('Outlet')

        if chargingStatus is not None and chargingStatus.chargingState.enabled:
            chargingStatus.chargingState.addObserver(self.onChargingState, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charOn = servOutlet.configure_char('On')
            # print(self.charOn.properties)
            # self.charOn.override_properties(properties={'Format': 'bool', 'Permissions': ['pr', 'ev']})
            self.setOnState(chargingStatus.chargingState)

        # if chargingStatus is not None and chargingStatus.remainingChargingTimeToComplete_min.enabled:
        #     chargingStatus.remainingChargingTimeToComplete_min.addObserver(self.onRemainingChargingTimeToComplete,
        #                                                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED)
        #     # Add Characteristic that is not planned for the service. This is still visible in other Apps than Apple Home
        #     servOutlet.add_characteristic(pyhap.loader.get_loader().get_char("RemainingDuration"))
        #     self.charRemainingDuration = servOutlet.configure_char('RemainingDuration')
        #     self.charRemainingDuration.set_value(chargingStatus.remainingChargingTimeToComplete_min.value * 60)

        if plugStatus is not None and plugStatus.plugConnectionState.enabled:
            plugStatus.plugConnectionState.addObserver(self.onplugConnectionStateChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charOutletInUse = servOutlet.configure_char('OutletInUse')
            self.setOutletInUse(plugStatus.plugConnectionState)

    def setOnState(self, chargingState):
        if self.charOn is not None:
            if chargingState.value == ChargingStatus.ChargingState.OFF \
                    or chargingState.value == ChargingStatus.ChargingState.READY_FOR_CHARGING:
                self.charOn.set_value(0)
            elif chargingState.value == ChargingStatus.ChargingState.CHARGING:
                self.charOn.set_value(1)
            elif chargingState.value == ChargingStatus.ChargingState.ERROR:
                self.charOn.set_value(0)
            else:
                self.charOn.set_value(0)
                LOG.warn('unsupported chargingState: %s', chargingState.value.value)

    def setOutletInUse(self, plugConnectionState):
        if self.charOutletInUse is not None:
            if plugConnectionState.value == PlugStatus.PlugConnectionState.CONNECTED:
                self.charOutletInUse.set_value(True)
            elif plugConnectionState.value == PlugStatus.PlugConnectionState.DISCONNECTED:
                self.charOutletInUse.set_value(False)
            else:
                self.charOutletInUse.set_value(False)
                LOG.warn('unsupported chargingState: %s', plugConnectionState.value.value)

    def onChargingState(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setOnState(element)
            LOG.debug('Charging State Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def onplugConnectionStateChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setOutletInUse(element)
            LOG.debug('Plug connection state Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def onRemainingChargingTimeToComplete(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charRemainingDuration.set_value(element.value * 60)
            LOG.debug('RemainingChargingTimeToComplete Changed: %d %%', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)
