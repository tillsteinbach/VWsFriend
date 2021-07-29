import logging

import pyhap

from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class Climatization(pyhap.accessory.Accessory):
    """Climatization Assessory"""

    category = pyhap.const.CATEGORY_THERMOSTAT

    def __init__(self, driver, displayName, climatizationStatus, climatizationSettings=None):
        super().__init__(driver=driver, display_name=displayName)

        servThermostat = self.add_preload_service('Thermostat')

        if climatizationStatus.climatisationState.enabled:
            climatizationStatus.climatisationState.addObserver(self.onClimatizationState,
                                                               AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charCurrentHeatingCoolingState = servThermostat.configure_char('CurrentHeatingCoolingState')
            self.setCurrentHeatingCoolingState(climatizationStatus.climatisationState)
            self.charTargetHeatingCoolingState = servThermostat.configure_char('TargetHeatingCoolingState')

        if climatizationSettings is not None and climatizationSettings.targetTemperature_C.enabled:
            climatizationSettings.targetTemperature_C.addObserver(self.onTargetTemperatureChange,
                                                                  AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charTargetTemperature = servThermostat.configure_char('TargetTemperature')
            self.charTargetTemperature.set_value(climatizationSettings.targetTemperature_C.value)

        # Set constant to celsius
        # TODO: We can enable conversion here later
        self.charTemperatureDisplayUnits = servThermostat.configure_char('TemperatureDisplayUnits')
        self.charTemperatureDisplayUnits.set_value(0)

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
            LOG.debug('targetTemperature_C Changed: %d %%', element.value)
        else:
            LOG.debug('Unsupported event %s', flags)
