import logging
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError

from vwsfriend.model.warning_light import WarningLight

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class WarningLightAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = session.merge(vehicle)
        self.enabledLights = session.query(WarningLight).filter(and_(WarningLight.vehicle == vehicle,
                                                                     WarningLight.end.is_(None))).order_by(WarningLight.start.desc()).all()
        LOG.info(f'Vehicle {self.vehicle.vin} has still {len(self.enabledLights)} warning lights on in the database.')

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('vehicleHealthWarnings', 'warningLights') \
                    and self.vehicle.weConnectVehicle.domains['vehicleHealthWarnings']['warningLights'].enabled:
                self.vehicle.weConnectVehicle.domains['vehicleHealthWarnings']['warningLights'].carCapturedTimestamp.addObserver(
                    self.__onCarCapturedTimestampChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(self.vehicle.weConnectVehicle.domains['vehicleHealthWarnings']['warningLights'].carCapturedTimestamp, None)

    def __onCarCapturedTimestampChange(self, element, flags):  # noqa: C901
        if self.enabledLights is not None:
            try:
                for enabledLight in self.enabledLights:
                    self.session.refresh(enabledLight)
            except ObjectDeletedError:
                LOG.warning('Last warning light entry was deleted')
                self.enabledLights = self.session.query(WarningLight).filter(and_(WarningLight.vehicle == self.vehicle,
                                                                                  WarningLight.end.is_(None))).order_by(WarningLight.start.desc()).all()
            except InvalidRequestError:
                LOG.warning('Last warning light entry was not persisted')
                self.enabledLights = self.session.query(WarningLight).filter(and_(WarningLight.vehicle == self.vehicle,
                                                                                  WarningLight.end.is_(None))).order_by(WarningLight.start.desc()).all()

        if element is not None and element.value is not None:
            warningLightsStatus = self.vehicle.weConnectVehicle.domains['vehicleHealthWarnings']['warningLights']
            for warningLight in warningLightsStatus.warningLights.values():
                if warningLight.messageId.value not in [light.messageId for light in self.enabledLights]:
                    warningLightEntry = WarningLight(self.vehicle, warningLight.messageId.value, element.value, warningLight.text.value,
                                                     warningLight.category.value)
                    LOG.info(f'Warning light {warningLight.messageId.value} in vehicle {self.vehicle.vin} turned on')

                    if warningLightsStatus.mileage_km.enabled:
                        warningLightEntry.start_mileage = warningLightsStatus.mileage_km.value
                    if warningLight.serviceLead.enabled:
                        warningLightEntry.serviceLead = warningLight.serviceLead.value
                    if warningLight.customerRelevance.enabled:
                        warningLightEntry.customerRelevance = warningLight.customerRelevance.value
                    if warningLight.priority.enabled:
                        warningLightEntry.priority = warningLight.priority.value

                    try:
                        self.session.add(warningLightEntry)
                    except IntegrityError as err:
                        LOG.warning('Could not add warning light entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
            with self.session.begin_nested():
                for enabledLight in self.enabledLights:
                    if enabledLight.messageId not in warningLightsStatus.warningLights:
                        enabledLight.end = element.value

                        if warningLightsStatus.mileage_km.enabled:
                            enabledLight.end_mileage = warningLightsStatus.mileage_km.value
                        LOG.info(f'Warning light {enabledLight.messageId} in vehicle {self.vehicle.vin} turned off')
            self.session.commit()

            self.enabledLights = self.session.query(WarningLight).filter(and_(WarningLight.vehicle == self.vehicle,
                                                                              WarningLight.end.is_(None))).order_by(WarningLight.start.desc()).all()

    def commit(self):
        self.session.commit()
