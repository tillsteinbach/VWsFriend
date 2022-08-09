import logging

import pyhap

from weconnect.addressable import AddressableLeaf
from weconnect.elements.access_status import AccessStatus
from weconnect.elements.control_operation import AccessControlOperation
from weconnect.errors import SetterError

from vwsfriend.homekit.genericAccessory import GenericAccessory

LOG = logging.getLogger("VWsFriend")


class LockingSystem(GenericAccessory):
    """LockingSystem Accessory"""

    category = pyhap.const.CATEGORY_DOOR_LOCK

    def __init__(self, driver, bridge, aid, id, vin, displayName, accessStatus, accessControl):
        super().__init__(driver=driver, bridge=bridge, displayName=displayName, aid=aid, vin=vin, id=id)

        self.accessControl = accessControl
        self.service = self.add_preload_service('LockMechanism', ['Name', 'ConfiguredName', 'LockCurrentState', 'LockTargetState'])

        if accessStatus is not None and accessStatus.overallStatus.enabled:
            accessStatus.overallStatus.addObserver(self.onOverallStatusChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            self.charLockCurrentState = self.service.configure_char('LockCurrentState')
            self.charLockTargetState = self.service.configure_char('LockTargetState', setter_callback=self.__onLockTargetStateChanged)
            self.charLockTargetState.allow_invalid_client_values = True
            self.setLockCurrentState(accessStatus.overallStatus)

        self.addNameCharacteristics()

    def setLockCurrentState(self, overallStatus):
        if self.charLockCurrentState is not None:
            if overallStatus.value == AccessStatus.OverallState.SAFE:
                self.charLockCurrentState.set_value(1)
                self.charLockTargetState.set_value(1)
            elif overallStatus.value == AccessStatus.OverallState.UNSAFE:
                self.charLockCurrentState.set_value(0)
                self.charLockTargetState.set_value(0)
            elif overallStatus.value == AccessStatus.OverallState.INVALID:
                self.charLockCurrentState.set_value(3)
                self.charLockTargetState.set_value(1)
            else:
                self.charLockCurrentState.set_value(3)
                self.charLockTargetState.set_value(1)
                LOG.warn('unsupported overallStatus: %s', overallStatus.value.value)

    def onOverallStatusChange(self, element, flags):
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            self.setLockCurrentState(element)
            LOG.debug('Overall access state Changed: %s', element.value.value)
        else:
            LOG.debug('Unsupported event %s', flags)

    def __onLockTargetStateChanged(self, value):
        if self.accessControl is not None and self.accessControl.enabled:
            try:
                if value == 1:
                    LOG.info('Lock car')
                    self.accessControl.value = AccessControlOperation.LOCK
                elif value == 0:
                    LOG.info('Unlock car')
                    self.accessControl.value = AccessControlOperation.UNLOCK
                else:
                    LOG.error('Input for lock target not understood: %d', value)
            except SetterError as setterError:
                LOG.error('Error locking or unlocking: %s', setterError)
                if self.charLockCurrentState.value in [1, 3]:
                    self.charLockTargetState.set_value(1)
                else:
                    self.charLockTargetState.set_value(0)
                self.setStatusFault(1, timeout=120)
        else:
            LOG.error('Locking cannot be controlled')
            if self.charLockCurrentState.value in [1, 3]:
                self.charLockTargetState.set_value(1)
            else:
                self.charLockTargetState.set_value(0)
            self.setStatusFault(1, timeout=120)
