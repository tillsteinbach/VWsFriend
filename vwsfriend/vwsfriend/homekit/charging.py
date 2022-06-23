import logging

import pyhap

from weconnect.addressable import AddressableLeaf
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.plug_status import PlugStatus
from weconnect.elements.control_operation import ControlOperation
from weconnect.errors import SetterError

from vwsfriend.homekit.genericAccessory import GenericAccessory

LOG = logging.getLogger("VWsFriend")


class Charging(GenericAccessory):
    """Charging Accessory"""

    category = pyhap.const.CATEGORY_OUTLET

    def __init__(self, driver, bridge, aid, id, vin, displayName, chargingStatus, plugStatus=None, batteryStatus=None, chargingControl=None):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.chargingControl = chargingControl

        self.service = self.add_preload_service('Outlet', ['Name', 'ConfiguredName', 'On', 'OutletInUse', 'RemainingDuration', 'Consumption', 'StatusFault'])
        self.batteryService = self.add_preload_service('BatteryService', ['BatteryLevel', 'StatusLowBattery', 'ChargingState'])
        self.service.add_linked_service(self.batteryService)

        if chargingStatus is not None and chargingStatus.chargingState.enabled:
            chargingStatus.chargingState.addObserver(self.onChargingState, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charOn = self.service.configure_char('On', setter_callback=self.__onOnChanged)
            self.setOnState(chargingStatus.chargingState)

        if chargingStatus is not None and chargingStatus.remainingChargingTimeToComplete_min.enabled:
            chargingStatus.remainingChargingTimeToComplete_min.addObserver(self.onRemainingChargingTimeToComplete,
                                                                           AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            # Add Characteristic that is not planned for the service. This is still visible in other Apps than Apple Home
            self.charRemainingDuration = self.service.configure_char('RemainingDuration', value=chargingStatus.remainingChargingTimeToComplete_min.value * 60)

        if chargingStatus is not None and chargingStatus.chargePower_kW.enabled:
            chargingStatus.chargePower_kW.addObserver(self.onChargePowerChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charWatt = self.service.configure_char('Consumption', value=chargingStatus.chargePower_kW.value * 1000)

        if plugStatus is not None and plugStatus.plugConnectionState.enabled:
            plugStatus.plugConnectionState.addObserver(self.onplugConnectionStateChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charOutletInUse = self.service.configure_char('OutletInUse')
            self.setOutletInUse(plugStatus.plugConnectionState)

        if batteryStatus is not None and batteryStatus.currentSOC_pct.enabled:
            batteryStatus.currentSOC_pct.addObserver(self.onCurrentSOCChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charBatteryLevel = self.batteryService.configure_char('BatteryLevel')
            self.charBatteryLevel.set_value(batteryStatus.currentSOC_pct.value)
            self.charStatusLowBattery = self.batteryService.configure_char('StatusLowBattery')
            self.setStatusLowBattery(batteryStatus.currentSOC_pct)

        if batteryStatus is not None and chargingStatus is not None and chargingStatus.chargingState.enabled:
            self.charChargingState = self.batteryService.configure_char('ChargingState')
            self.setChargingState(chargingStatus.chargingState)

        self.addNameCharacteristics()
        self.addStatusFaultCharacteristic()

    def setOnState(self, chargingState):
        if self.charOn is not None:
            if chargingState.value in (ChargingStatus.ChargingState.OFF,
                                       ChargingStatus.ChargingState.READY_FOR_CHARGING,
                                       ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING,
                                       ChargingStatus.ChargingState.NOT_READY_FOR_CHARGING):
                self.charOn.set_value(0)
            elif chargingState.value in (ChargingStatus.ChargingState.CHARGING,
                                         ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION,
                                         ChargingStatus.ChargingState.CONSERVATION):
                self.charOn.set_value(1)
            elif chargingState.value in (ChargingStatus.ChargingState.ERROR,
                                         ChargingStatus.ChargingState.UNSUPPORTED):
                self.charOn.set_value(0)
            else:
                self.charOn.set_value(0)
                LOG.warn('unsupported chargingState: %s', chargingState.value.value)

    def setOutletInUse(self, plugConnectionState):
        if self.charOutletInUse is not None:
            if plugConnectionState.value == PlugStatus.PlugConnectionState.CONNECTED:
                self.charOutletInUse.set_value(True)
            elif plugConnectionState.value in (PlugStatus.PlugConnectionState.DISCONNECTED,
                                               PlugStatus.PlugConnectionState.INVALID,
                                               PlugStatus.PlugConnectionState.UNSUPPORTED):
                self.charOutletInUse.set_value(False)
            else:
                self.charOutletInUse.set_value(False)
                LOG.warn('unsupported plugConnectionState: %s', plugConnectionState.value.value)

    def onChargingState(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setOnState(element)
            self.setChargingState(element)
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

    def onChargePowerChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charWatt.set_value(element.value * 1000)
            LOG.debug('chargePower_kW Changed: %d', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def __onOnChanged(self, value):
        if self.chargingControl.enabled:
            try:
                if value:
                    LOG.info('Switch charging on')
                    self.chargingControl.value = ControlOperation.START
                else:
                    LOG.info('Switch charging off')
                    self.chargingControl.value = ControlOperation.STOP
            except SetterError as setterError:
                LOG.error('Error starting charging: %s', setterError)
                self.setStatusFault(1, timeout=120)
        else:
            LOG.error('Charging cannot be controled')

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

    def onCurrentSOCChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charBatteryLevel.set_value(element.value)
            self.setStatusLowBattery(element)
            LOG.debug('Battery SoC Changed: %d %%', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)
