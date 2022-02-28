import logging

import pyhap

from weconnect.addressable import AddressableLeaf
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.control_operation import ControlOperation
from weconnect.errors import SetterError

from vwsfriend.homekit.genericAccessory import GenericAccessory


LOG = logging.getLogger("VWsFriend")


class Climatization(GenericAccessory):
    """Climatization Accessory"""

    category = pyhap.const.CATEGORY_AIR_CONDITIONER

    def __init__(self, driver, bridge, aid, id, vin, displayName, climatizationStatus: ClimatizationStatus, climatizationSettings=None,
                 batteryStatus=None, chargingStatus=None, climatizationControl=None):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.climatizationControl = climatizationControl
        self.climatizationSettings = climatizationSettings
        self.climatizationStatus = climatizationStatus
        self.service = self.add_preload_service('Thermostat', ['Name', 'ConfiguredName', 'CurrentHeatingCoolingState', 'TargetHeatingCoolingState',
                                                'TargetTemperature', 'TemperatureDisplayUnits', 'RemainingDuration', 'StatusFault'])
        self.batteryService = self.add_preload_service('BatteryService', ['BatteryLevel', 'StatusLowBattery', 'ChargingState'])
        self.service.add_linked_service(self.batteryService)

        if climatizationStatus.climatisationState.enabled:
            climatizationStatus.climatisationState.addObserver(self.onClimatizationState,
                                                               AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charTargetHeatingCoolingState = self.service.configure_char('TargetHeatingCoolingState',
                                                                             valid_values={'Auto': 3, 'Off': 0},
                                                                             setter_callback=self.__onTargetHeatingCoolingStateChanged)
            self.charTargetHeatingCoolingState.allow_invalid_client_values = True
            self.charCurrentHeatingCoolingState = self.service.configure_char('CurrentHeatingCoolingState')

            climatizationStatus.remainingClimatisationTime_min.addObserver(self.onRemainingClimatisationTime,
                                                                           AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            # Add Characteristic that is not planned for the service. This is still visible in other Apps than Apple Home
            remainingTime = 0
            if climatizationStatus.climatisationState.value in [ClimatizationStatus.ClimatizationState.HEATING,
                                                                ClimatizationStatus.ClimatizationState.COOLING,
                                                                ClimatizationStatus.ClimatizationState.VENTILATION] \
                    and climatizationStatus.remainingClimatisationTime_min.enabled:
                remainingTime = climatizationStatus.remainingClimatisationTime_min.value * 60
            self.charRemainingDuration = self.service.configure_char('RemainingDuration', value=remainingTime)

            self.setCurrentHeatingCoolingState(climatizationStatus.climatisationState)

        if climatizationSettings is not None and climatizationSettings.targetTemperature_C.enabled:
            climatizationSettings.targetTemperature_C.addObserver(self.onTargetTemperatureChange,
                                                                  AddressableLeaf.ObserverEvent.VALUE_CHANGED)
        elif climatizationSettings is not None and climatizationSettings.targetTemperature_K.enabled:
            climatizationSettings.targetTemperature_K.addObserver(self.onTargetTemperatureChange,
                                                                  AddressableLeaf.ObserverEvent.VALUE_CHANGED)

        self.charTargetTemperature = self.service.configure_char('TargetTemperature', value=self.getTemperature(),
                                                                 properties={'maxValue': 29.5, 'minStep': 0.5, 'minValue': 16},
                                                                 setter_callback=self.__onTargetTemperatureChanged)

        if batteryStatus is not None and batteryStatus.currentSOC_pct.enabled:
            batteryStatus.currentSOC_pct.addObserver(self.onCurrentSOCChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charBatteryLevel = self.batteryService.configure_char('BatteryLevel')
            self.charBatteryLevel.set_value(batteryStatus.currentSOC_pct.value)
            self.charStatusLowBattery = self.batteryService.configure_char('StatusLowBattery')
            self.setStatusLowBattery(batteryStatus.currentSOC_pct)

        if batteryStatus is not None and chargingStatus is not None and chargingStatus.chargingState.enabled:
            chargingStatus.chargingState.addObserver(self.onChargingState, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charChargingState = self.batteryService.configure_char('ChargingState')
            self.setChargingState(chargingStatus.chargingState)

        # Set constant to celsius
        # TODO: We can enable conversion here later
        self.charTemperatureDisplayUnits = self.service.configure_char('TemperatureDisplayUnits')
        self.charTemperatureDisplayUnits.set_value(0)

        self.addNameCharacteristics()
        self.addStatusFaultCharacteristic()

    def getTemperature(self):
        if self.climatizationSettings.targetTemperature_C is not None and self.climatizationSettings.targetTemperature_C.enabled:
            return self.climatizationSettings.targetTemperature_C.value
        elif self.climatizationSettings.targetTemperature_K is not None and self.climatizationSettings.targetTemperature_K.enabled:
            return (self.climatizationSettings.targetTemperature_K.value - 273.15)
        temperature = self.bridge.getConfigItem(self.id, self.vin, 'TargetTemperature')
        if temperature is not None:
            return float(temperature)
        return 20.5

    def setTemperature(self, temperature):
        if self.climatizationSettings.targetTemperature_C is not None and self.climatizationSettings.targetTemperature_C.enabled:
            self.climatizationSettings.targetTemperature_C.value = temperature
        elif self.climatizationSettings.targetTemperature_K is not None and self.climatizationSettings.targetTemperature_K.enabled:
            self.climatizationSettings.targetTemperature_K.value = (temperature + 273.15)
        self.bridge.setConfigItem(self.id, self.vin, 'TargetTemperature', temperature)
        self.bridge.persistConfig()

    def setCurrentHeatingCoolingState(self, climatisationState):
        if self.charCurrentHeatingCoolingState is not None:
            if climatisationState.value == ClimatizationStatus.ClimatizationState.HEATING:
                self.charCurrentHeatingCoolingState.set_value(1)
                self.charTargetHeatingCoolingState.set_value(3)
            elif climatisationState.value == ClimatizationStatus.ClimatizationState.COOLING \
                    or climatisationState.value == ClimatizationStatus.ClimatizationState.VENTILATION:
                self.charCurrentHeatingCoolingState.set_value(2)
                self.charTargetHeatingCoolingState.set_value(3)
            elif climatisationState.value == ClimatizationStatus.ClimatizationState.OFF:
                self.charCurrentHeatingCoolingState.set_value(0)
                self.charTargetHeatingCoolingState.set_value(0)
            else:
                self.charCurrentHeatingCoolingState.set_value(0)
                self.charTargetHeatingCoolingState.set_value(0)
                LOG.warn('unsupported climatisationState: %s', climatisationState.value.value)
        if climatisationState.value in [ClimatizationStatus.ClimatizationState.HEATING,
                                        ClimatizationStatus.ClimatizationState.COOLING,
                                        ClimatizationStatus.ClimatizationState.VENTILATION] \
                and self.climatizationStatus.remainingClimatisationTime_min.enabled:
            self.charRemainingDuration.set_value(self.climatizationStatus.remainingClimatisationTime_min.value * 60)
        else:
            self.charRemainingDuration.set_value(0)

    def onClimatizationState(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setCurrentHeatingCoolingState(element)
            LOG.debug('Climatization State Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def onTargetTemperatureChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charTargetTemperature.set_value(self.getTemperature())
            LOG.info('targetTemperature Changed: %f', self.getTemperature())
        else:
            LOG.debug('Unsupported event %s', flags)

    def onRemainingClimatisationTime(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            if self.climatizationStatus.climatisationState.value in [ClimatizationStatus.ClimatizationState.HEATING,
                                                                     ClimatizationStatus.ClimatizationState.COOLING,
                                                                     ClimatizationStatus.ClimatizationState.VENTILATION]:
                self.charRemainingDuration.set_value(element.value * 60)
            else:
                self.charRemainingDuration.set_value(0)
            LOG.debug('RemainingClimatisationTime Changed: %d', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def __onTargetHeatingCoolingStateChanged(self, value):
        if self.climatizationControl.enabled:
            try:
                if value == 1 or value == 2 or value == 3:
                    LOG.info('Switch climatization on')
                    self.climatizationControl.value = self.getTemperature()
                elif value == 0:
                    LOG.info('Switch climatization off')
                    self.climatizationControl.value = ControlOperation.STOP
                else:
                    LOG.error('Input for climatization not understood: %d', value)
            except SetterError as setterError:
                LOG.error('Error starting climatization: %s', setterError)
                if self.charCurrentHeatingCoolingState.value in [1, 2]:
                    self.charTargetHeatingCoolingState.set_value(3)
                else:
                    self.charTargetHeatingCoolingState.set_value(0)
                self.setStatusFault(1, timeout=120)
        else:
            LOG.error('Climatization cannot be controled')

    def __onTargetTemperatureChanged(self, value):
        if self.climatizationSettings.enabled:
            try:
                LOG.info('Change climatization target temperature to: %f', value)
                self.setTemperature(value)
            except SetterError as setterError:
                LOG.error('Error setting target temperature: %s', setterError)
                self.setStatusFault(1, timeout=120)
            if self.charTargetHeatingCoolingState.value in [1, 2, 3]:
                LOG.info('Restart climatisation with new temperature: %f', value)
                self.climatizationControl.value = value
        else:
            LOG.error('Climatization target temperature cannot be controled')

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
