import logging

import pyhap

from weconnect.addressable import AddressableLeaf
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.control_operation import ControlOperation

from vwsfriend.homekit.genericAccessory import GenericAccessory


LOG = logging.getLogger("VWsFriend")


class Climatization(GenericAccessory):
    """Climatization Accessory"""

    category = pyhap.const.CATEGORY_AIR_CONDITIONER

    def __init__(self, driver, bridge, aid, id, vin, displayName, climatizationStatus: ClimatizationStatus, climatizationSettings=None,
                 climatizationControl=None):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.climatizationControl = climatizationControl
        self.climatizationSettings = climatizationSettings
        self.service = self.add_preload_service('Thermostat', ['Name', 'ConfiguredName', 'CurrentHeatingCoolingState', 'TargetHeatingCoolingState',
                                                'TargetTemperature', 'TemperatureDisplayUnits', 'RemainingDuration'])

        if climatizationStatus.climatisationState.enabled:
            climatizationStatus.climatisationState.addObserver(self.onClimatizationState,
                                                               AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charCurrentHeatingCoolingState = self.service.configure_char('CurrentHeatingCoolingState')
            self.setCurrentHeatingCoolingState(climatizationStatus.climatisationState)
            self.charTargetHeatingCoolingState = self.service.configure_char('TargetHeatingCoolingState',
                                                                             setter_callback=self.__onTargetHeatingCoolingStateChanged)

            climatizationStatus.remainingClimatisationTime_min.addObserver(self.onRemainingClimatisationTime,
                                                                           AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            # Add Characteristic that is not planned for the service. This is still visible in other Apps than Apple Home
            self.charRemainingDuration = self.service.configure_char('RemainingDuration', value=climatizationStatus.remainingClimatisationTime_min.value * 60)

        if climatizationSettings is not None and climatizationSettings.targetTemperature_C.enabled:
            climatizationSettings.targetTemperature_C.addObserver(self.onTargetTemperatureChange,
                                                                  AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charTargetTemperature = self.service.configure_char('TargetTemperature', value=climatizationSettings.targetTemperature_C.value,
                                                                     setter_callback=self.__onTargetTemperatureChanged)

        # Set constant to celsius
        # TODO: We can enable conversion here later
        self.charTemperatureDisplayUnits = self.service.configure_char('TemperatureDisplayUnits')
        self.charTemperatureDisplayUnits.set_value(0)

        self.addNameCharacteristics()

    def setCurrentHeatingCoolingState(self, climatisationState):
        if self.charCurrentHeatingCoolingState is not None:
            if climatisationState.value == ClimatizationStatus.ClimatizationState.HEATING:
                self.charCurrentHeatingCoolingState.set_value(1)
            elif climatisationState.value == ClimatizationStatus.ClimatizationState.COOLING \
                    or climatisationState == ClimatizationStatus.ClimatizationState.VENTILATION:
                self.charCurrentHeatingCoolingState.set_value(2)
            elif climatisationState.value == ClimatizationStatus.ClimatizationState.OFF:
                self.charCurrentHeatingCoolingState.set_value(0)
            else:
                self.charCurrentHeatingCoolingState.set_value(0)
                LOG.warn('unsupported climatisationState: %s', climatisationState.value.value)

    def onClimatizationState(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setCurrentHeatingCoolingState(element)
            LOG.debug('Climatization State Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def onTargetTemperatureChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charTargetTemperature.set_value(element.value)
            LOG.info('targetTemperature_C Changed: %f', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def onRemainingClimatisationTime(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.charRemainingDuration.set_value(element.value * 60)
            LOG.debug('RemainingClimatisationTime Changed: %d', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def __onTargetHeatingCoolingStateChanged(self, value):
        if self.climatizationControl.enabled:
            if value == 1 or value == 2:
                LOG.info('Switch climatization on')
                self.climatizationControl.value = ControlOperation.START
            elif value == 0:
                LOG.info('Switch climatization off')
                self.climatizationControl.value = ControlOperation.STOP
            else:
                LOG.debug('Inout for climatization not understood: %d', value)
        else:
            LOG.error('Climatization cannot be controled')

    def __onTargetTemperatureChanged(self, value):
        if self.climatizationSettings.enabled:
            self.climatizationSettings.targetTemperature_C.value = value
            LOG.debug('Changed climatization target temperature to: %f', value)
        else:
            LOG.error('Climatization target temperature cannot be controled')
