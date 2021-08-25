import logging

import pyhap

from weconnect.addressable import AddressableLeaf
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.plug_status import PlugStatus
from weconnect.elements.control_operation import ControlOperation

from vwsfriend.homekit.genericAccessory import GenericAccessory

LOG = logging.getLogger("VWsFriend")


class Charging(GenericAccessory):
    """Charging Accessory"""

    category = pyhap.const.CATEGORY_OUTLET

    def __init__(self, driver, bridge, aid, id, vin, displayName, chargingStatus, plugStatus=None, chargingControl=None):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.chargingControl = chargingControl

        self.service = self.add_preload_service('Outlet', ['Name', 'ConfiguredName', 'On', 'OutletInUse', 'RemainingDuration'])

        if chargingStatus is not None and chargingStatus.chargingState.enabled:
            chargingStatus.chargingState.addObserver(self.onChargingState, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charOn = self.service.configure_char('On', setter_callback=self.__onOnChanged)
            # print(self.charOn.properties)
            # self.charOn.override_properties(properties={'Format': 'bool', 'Permissions': ['pr', 'ev']})
            self.setOnState(chargingStatus.chargingState)

        if chargingStatus is not None and chargingStatus.remainingChargingTimeToComplete_min.enabled:
            chargingStatus.remainingChargingTimeToComplete_min.addObserver(self.onRemainingChargingTimeToComplete,
                                                                           AddressableLeaf.ObserverEvent.VALUE_CHANGED)

            # Add Characteristic that is not planned for the service. This is still visible in other Apps than Apple Home
            self.charRemainingDuration = self.service.configure_char('RemainingDuration', value=chargingStatus.remainingChargingTimeToComplete_min.value * 60)

        if plugStatus is not None and plugStatus.plugConnectionState.enabled:
            plugStatus.plugConnectionState.addObserver(self.onplugConnectionStateChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charOutletInUse = self.service.configure_char('OutletInUse')
            self.setOutletInUse(plugStatus.plugConnectionState)

        self.addNameCharacteristics()

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
                LOG.warn('unsupported plugConnectionState: %s', plugConnectionState.value.value)

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
            LOG.debug('RemainingChargingTimeToComplete Changed: %d', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def __onOnChanged(self, value):
        if self.chargingControl.enabled:
            if value:
                LOG.debug('Switch charging on')
                self.chargingControl.value = ControlOperation.START
            else:
                LOG.debug('Switch charging off')
                self.chargingControl.value = ControlOperation.STOP
        else:
            LOG.error('Charging cannot be controled')
