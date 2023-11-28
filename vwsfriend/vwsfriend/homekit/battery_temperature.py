import logging

import pyhap

from weconnect.elements.charging_status import ChargingStatus
from weconnect.addressable import AddressableLeaf
from weconnect.util import kelvinToCelsius

from vwsfriend.homekit.genericAccessory import GenericAccessory

LOG = logging.getLogger("VWsFriend")


class BatteryTemperature(GenericAccessory):
    """BatteryTemperature Accessory"""

    category = pyhap.const.CATEGORY_OTHER

    def __init__(self, driver, bridge, aid, id, vin, displayName, batteryStatus, batteryTemperatureStatus, chargingStatus=None):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.service = self.add_preload_service('TemperatureSensor', ['Name', 'ConfiguredName', 'BatteryLevel', 'StatusLowBattery', 'ChargingState',
                                                                      'CurrentTemperature'])
        self.batteryTemperatureStatus = None

        if batteryStatus.currentSOC_pct.enabled:
            batteryStatus.currentSOC_pct.addObserver(self.onCurrentSOCChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charBatteryLevel = self.service.configure_char('BatteryLevel')
            self.charBatteryLevel.set_value(batteryStatus.currentSOC_pct.value)
            self.charStatusLowBattery = self.service.configure_char('StatusLowBattery')
            self.setStatusLowBattery(batteryStatus.currentSOC_pct)

        if chargingStatus is not None and chargingStatus.chargingState.enabled:
            chargingStatus.chargingState.addObserver(self.onChargingState, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charChargingState = self.service.configure_char('ChargingState')
            self.setChargingState(chargingStatus.chargingState)

        if batteryTemperatureStatus is not None and batteryTemperatureStatus.temperatureHvBatteryMin_K.enabled \
                and batteryTemperatureStatus.temperatureHvBatteryMax_K.enabled:
            self.batteryTemperatureStatus = batteryTemperatureStatus
            batteryTemperatureStatus.addObserver(self.onBatteryTemperatureChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charTemperature = self.service.configure_char('CurrentTemperature')
            if batteryTemperatureStatus.temperatureHvBatteryMin_K.enabled and batteryTemperatureStatus.temperatureHvBatteryMax_K.enabled:
                self.setBatteryTemperature(batteryTemperatureStatus.temperatureHvBatteryMin_K.value, batteryTemperatureStatus.temperatureHvBatteryMax_K.value)

        self.addNameCharacteristics()

    def setStatusLowBattery(self, currentSOC_pct):
        if self.charStatusLowBattery is not None:
            if currentSOC_pct.value > 10:
                self.charStatusLowBattery.set_value(0)
            else:
                self.charStatusLowBattery.set_value(1)

    def setChargingState(self, chargingState):
        if self.charChargingState is not None:
            if chargingState.value in (ChargingStatus.ChargingState.OFF,
                                       ChargingStatus.ChargingState.READY_FOR_CHARGING,
                                       ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING,
                                       ChargingStatus.ChargingState.NOT_READY_FOR_CHARGING):
                self.charChargingState.set_value(0)
            elif chargingState.value in (ChargingStatus.ChargingState.CHARGING,
                                         ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION,
                                         ChargingStatus.ChargingState.CONSERVATION):
                self.charChargingState.set_value(1)
            elif chargingState.value in (ChargingStatus.ChargingState.ERROR,
                                         ChargingStatus.ChargingState.UNSUPPORTED):
                self.charChargingState.set_value(2)
            else:
                self.charChargingState.set_value(2)
                LOG.warn('unsupported chargingState: %s', chargingState.value.value)

    def setBatteryTemperature(self, temperatureHvBatteryMin_K, temperatureHvBatteryMax_K):
        if self.charTemperature is not None:
            temperature = (kelvinToCelsius(temperatureHvBatteryMin_K) + kelvinToCelsius(temperatureHvBatteryMax_K)) / 2
            self.charTemperature.set_value(temperature)

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

    def onBatteryTemperatureChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED and self.batteryTemperatureStatus is not None \
                and self.batteryTemperatureStatus.temperatureHvBatteryMin_K.enabled and self.batteryTemperatureStatus.temperatureHvBatteryMax_K.enabled:
            self.setBatteryTemperature(self.batteryTemperatureStatus.temperatureHvBatteryMin_K.value,
                                       self.batteryTemperatureStatus.temperatureHvBatteryMax_K.value)
            LOG.debug('Battery temperature Changed: %f to %f °C', self.batteryTemperatureStatus.temperatureHvBatteryMin_K.value,
                      self.batteryTemperatureStatus.temperatureHvBatteryMax_K.value)
        else:
            LOG.debug('Unsupported event %s', flags)
