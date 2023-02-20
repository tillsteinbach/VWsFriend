import logging
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError

from vwsfriend.model.climatization import Climatization

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class ClimatizationAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = session.merge(vehicle)
        self.climate = session.query(Climatization).filter(and_(Climatization.vehicle == vehicle,
                                                                Climatization.carCapturedTimestamp.isnot(None))) \
                                                   .order_by(Climatization.carCapturedTimestamp.desc()).first()

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('climatisation', 'climatisationStatus') \
                    and self.vehicle.weConnectVehicle.domains['climatisation']['climatisationStatus'].enabled:
                self.vehicle.weConnectVehicle.domains['climatisation']['climatisationStatus'].carCapturedTimestamp.addObserver(
                    self.__onCarCapturedTimestampChange,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(self.vehicle.weConnectVehicle.domains['climatisation']['climatisationStatus'].carCapturedTimestamp, None)

    def __onCarCapturedTimestampChange(self, element, flags):  # noqa: C901
        if element is not None and element.value is not None:
            climateStatus = self.vehicle.weConnectVehicle.domains['climatisation']['climatisationStatus']
            current_remainingClimatisationTime_min = None
            current_climatisationState = None
            if climateStatus.remainingClimatisationTime_min.enabled:
                current_remainingClimatisationTime_min = climateStatus.remainingClimatisationTime_min.value
            if climateStatus.climatisationState.enabled:
                current_climatisationState = climateStatus.climatisationState.value

            if self.climate is not None:
                try:
                    self.session.refresh(self.climate)
                except ObjectDeletedError:
                    LOG.warning('Last climatisation entry was deleted')
                    self.climate = self.session.query(Climatization).filter(and_(Climatization.vehicle == self.vehicle,
                                                                                 Climatization.carCapturedTimestamp.isnot(None))) \
                        .order_by(Climatization.carCapturedTimestamp.desc()).first()
                except InvalidRequestError:
                    LOG.warning('Last climatisation entry was not persisted')
                    self.climate = self.session.query(Climatization).filter(and_(Climatization.vehicle == self.vehicle,
                                                                                 Climatization.carCapturedTimestamp.isnot(None))) \
                        .order_by(Climatization.carCapturedTimestamp.desc()).first()

            if self.climate is None or (self.climate.carCapturedTimestamp != climateStatus.carCapturedTimestamp.value and (
                    self.climate.remainingClimatisationTime_min != current_remainingClimatisationTime_min
                    or self.climate.climatisationState != current_climatisationState)):

                self.climate = Climatization(self.vehicle, climateStatus.carCapturedTimestamp.value, current_remainingClimatisationTime_min,
                                             current_climatisationState)
                with self.session.begin_nested():
                    try:
                        self.session.add(self.climate)
                    except IntegrityError as err:
                        LOG.warning('Could not add climatization entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                self.session.commit()

    def commit(self):
        self.session.commit()
