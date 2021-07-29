import logging

import pyhap

from weconnect.elements.charging_status import ChargingStatus
from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class Battery(pyhap.accessory.Accessory):
    """Battery Assessory"""

    category = pyhap.const.CATEGORY_OTHER

    def __init__(self, driver, displayName, batteryStatus, chargingStatus=None):
        super().__init__(driver=driver, display_name=displayName)

        servBattery = self.add_preload_service('BatteryService')

        if batteryStatus.currentSOC_pct.enabled:
            batteryStatus.currentSOC_pct.addObserver(self.onCurrentSOCChange,
                                                     AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charBatteryLevel = servBattery.configure_char('BatteryLevel')
            self.charBatteryLevel.set_value(batteryStatus.currentSOC_pct.value)
            self.charStatusLowBattery = servBattery.configure_char('StatusLowBattery')
            self.setStatusLowBattery(batteryStatus.currentSOC_pct)

        if chargingStatus is not None and chargingStatus.chargingState.enabled:
            chargingStatus.chargingState.addObserver(self.onChargingState, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charChargingState = servBattery.configure_char('ChargingState')
            self.setChargingState(chargingStatus.chargingState)

    def setStatusLowBattery(self, currentSOC_pct):
        if self.charStatusLowBattery is not None:
            if currentSOC_pct.value > 10:
                self.charStatusLowBattery.set_value(0)
            else:
                self.charStatusLowBattery.set_value(1)

    def setChargingState(self, chargingState):
        if self.charChargingState is not None:
            if chargingState.value == ChargingStatus.ChargingState.OFF \
                    or chargingState.value == ChargingStatus.ChargingState.READY_FOR_CHARGING:
                self.charChargingState.set_value(0)
            elif chargingState.value == ChargingStatus.ChargingState.CHARGING:
                self.charChargingState.set_value(1)
            elif chargingState.value == ChargingStatus.ChargingState.ERROR:
                self.charChargingState.set_value(2)
            else:
                self.charChargingState.set_value(2)
                LOG.warn('unsupported chargingState: %s', chargingState.value.value)

    def onCurrentSOCChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charBatteryLevel.set_value(element.value)
            self.setStatusLowBattery(element)
            LOG.debug('Battery SoC Changed: %d %%', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def onChargingState(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setChargingState(element)
            LOG.debug('Charging State Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)
