import logging
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError

from vwsfriend.model.maintenance import Maintenance, MaintenanceType

from weconnect.addressable import AddressableLeaf

LOG = logging.getLogger("VWsFriend")


class MaintenanceAgent():
    def __init__(self, session, vehicle):
        self.session = session
        self.vehicle = session.merge(vehicle)
        self.inspectionEntry = session.query(Maintenance).filter(and_(Maintenance.vehicle == vehicle,
                                                                      Maintenance.date.is_(None),
                                                                      Maintenance.type == MaintenanceType.INSPECTION)).first()
        self.oilServiceEntry = session.query(Maintenance).filter(and_(Maintenance.vehicle == vehicle,
                                                                      Maintenance.date.is_(None),
                                                                      Maintenance.type == MaintenanceType.OIL_SERVICE)).first()

        # register for updates:
        if self.vehicle.weConnectVehicle is not None:
            if self.vehicle.weConnectVehicle.statusExists('vehicleHealthInspection', 'maintenanceStatus') \
                    and self.vehicle.weConnectVehicle.domains['vehicleHealthInspection']['maintenanceStatus'].enabled:
                self.vehicle.weConnectVehicle.domains['vehicleHealthInspection']['maintenanceStatus'].carCapturedTimestamp.addObserver(
                    self.__onCarCapturedTimestampChange, AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True)
                self.__onCarCapturedTimestampChange(self.vehicle.weConnectVehicle.domains['vehicleHealthInspection']['maintenanceStatus'].carCapturedTimestamp,
                                                    None)

    def __onCarCapturedTimestampChange(self, element, flags):  # noqa: C901
        if self.inspectionEntry is not None:
            try:
                self.session.refresh(self.inspectionEntry)
            except ObjectDeletedError:
                LOG.warning('Last inspection entry was deleted')
                self.inspectionEntry = self.session.query(Maintenance).filter(and_(Maintenance.vehicle == self.vehicle,
                                                                                   Maintenance.date.is_(None),
                                                                                   Maintenance.type == MaintenanceType.INSPECTION)).first()
            except InvalidRequestError:
                LOG.warning('Lastinspection entry was not persisted')
                self.inspectionEntry = self.session.query(Maintenance).filter(and_(Maintenance.vehicle == self.vehicle,
                                                                                   Maintenance.date.is_(None),
                                                                                   Maintenance.type == MaintenanceType.INSPECTION)).first()
        if self.oilServiceEntry is not None:
            try:
                self.session.refresh(self.oilServiceEntry)
            except ObjectDeletedError:
                LOG.warning('Last oil service entry was deleted')
                self.oilServiceEntry = self.session.query(Maintenance).filter(and_(Maintenance.vehicle == self.vehicle,
                                                                                   Maintenance.date.is_(None),
                                                                                   Maintenance.type == MaintenanceType.OIL_SERVICE)).first()
            except InvalidRequestError:
                LOG.warning('Last oil service entry was not persisted')
                self.oilServiceEntry = self.session.query(Maintenance).filter(and_(Maintenance.vehicle == self.vehicle,
                                                                                   Maintenance.date.is_(None),
                                                                                   Maintenance.type == MaintenanceType.OIL_SERVICE)).first()

        if element is not None and element.value is not None:
            maintenanceStatus = self.vehicle.weConnectVehicle.domains['vehicleHealthInspection']['maintenanceStatus']

            if maintenanceStatus.inspectionDue_days.enabled and maintenanceStatus.inspectionDue_days.value is not None:
                if self.inspectionEntry is None:
                    self.inspectionEntry = Maintenance(self.vehicle, None, None, MaintenanceType.INSPECTION, maintenanceStatus.inspectionDue_days.value, None)
                    with self.session.begin_nested():
                        try:
                            self.session.add(self.inspectionEntry)
                        except IntegrityError as err:
                            LOG.warning('Could not add inspection entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                    self.session.commit()
                elif self.inspectionEntry.due_in_days is None:
                    with self.session.begin_nested():
                        self.inspectionEntry.due_in_days = maintenanceStatus.inspectionDue_days.value
                    self.session.commit()
                else:
                    if maintenanceStatus.inspectionDue_days.value > self.inspectionEntry.due_in_days:
                        with self.session.begin_nested():
                            self.inspectionEntry.date = element.value
                            if maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km.value is not None:
                                self.inspectionEntry.mileage = maintenanceStatus.mileage_km.value
                        self.session.commit()
                        LOG.info(f'Inspection of vehicle {self.vehicle.vin} done')
                        self.inspectionEntry = Maintenance(self.vehicle, None, None, MaintenanceType.INSPECTION, maintenanceStatus.inspectionDue_days.value,
                                                           None)
                        with self.session.begin_nested():
                            try:
                                self.session.add(self.inspectionEntry)
                            except IntegrityError as err:
                                LOG.warning('Could not add inspection entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                        self.session.commit()
                    else:
                        with self.session.begin_nested():
                            self.inspectionEntry.due_in_days = maintenanceStatus.inspectionDue_days.value
                        self.session.commit()

            if maintenanceStatus.inspectionDue_km.enabled and maintenanceStatus.inspectionDue_km.value is not None:
                if self.inspectionEntry is None:
                    self.inspectionEntry = Maintenance(self.vehicle, None, None, MaintenanceType.INSPECTION, None, maintenanceStatus.inspectionDue_km.value)
                    with self.session.begin_nested():
                        try:
                            self.session.add(self.inspectionEntry)
                        except IntegrityError as err:
                            LOG.warning('Could not add inspection entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                    self.session.commit()
                elif self.inspectionEntry.due_in_km is None:
                    with self.session.begin_nested():
                        self.inspectionEntry.due_in_km = maintenanceStatus.inspectionDue_km.value
                    self.session.commit()
                else:
                    if maintenanceStatus.inspectionDue_km.value > self.inspectionEntry.due_in_km:
                        with self.session.begin_nested():
                            self.inspectionEntry.date = element.value
                            if maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km.value is not None:
                                self.inspectionEntry.mileage = maintenanceStatus.mileage_km.value
                        self.session.commit()
                        LOG.info(f'Inspection of vehicle {self.vehicle.vin} done')
                        self.inspectionEntry = Maintenance(self.vehicle, None, None, MaintenanceType.INSPECTION, None,
                                                           maintenanceStatus.inspectionDue_km.value)
                        with self.session.begin_nested():
                            try:
                                self.session.add(self.inspectionEntry)
                            except IntegrityError as err:
                                LOG.warning('Could not add inspection entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                        self.session.commit()
                    else:
                        with self.session.begin_nested():
                            self.inspectionEntry.due_in_km = maintenanceStatus.inspectionDue_km.value
                        self.session.commit()

            if maintenanceStatus.oilServiceDue_days.enabled and maintenanceStatus.oilServiceDue_days.value is not None:
                if self.oilServiceEntry is None:
                    self.oilServiceEntry = Maintenance(self.vehicle, None, None, MaintenanceType.OIL_SERVICE, maintenanceStatus.oilServiceDue_days.value, None)
                    with self.session.begin_nested():
                        try:
                            self.session.add(self.oilServiceEntry)
                        except IntegrityError as err:
                            LOG.warning('Could not add oil service entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                    self.session.commit()
                elif self.oilServiceEntry.due_in_days is None:
                    with self.session.begin_nested():
                        self.oilServiceEntry.due_in_days = maintenanceStatus.oilServiceDue_days.value
                    self.session.commit()
                else:
                    if maintenanceStatus.oilServiceDue_days.value > self.oilServiceEntry.due_in_days:
                        with self.session.begin_nested():
                            self.oilServiceEntry.date = element.value
                            if maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km.value is not None:
                                self.oilServiceEntry.mileage = maintenanceStatus.mileage_km.value
                        self.session.commit()
                        LOG.info(f'Oil service for vehicle {self.vehicle.vin} done')
                        self.oilServiceEntry = Maintenance(self.vehicle, None, None, MaintenanceType.OIL_SERVICE, maintenanceStatus.oilServiceDue_days.value,
                                                           None)
                        with self.session.begin_nested():
                            try:
                                self.session.add(self.oilServiceEntry)
                            except IntegrityError as err:
                                LOG.warning('Could not add oil service entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                        self.session.commit()
                    else:
                        with self.session.begin_nested():
                            self.oilServiceEntry.due_in_days = maintenanceStatus.oilServiceDue_days.value
                        self.session.commit()

            if maintenanceStatus.oilServiceDue_km.enabled and maintenanceStatus.oilServiceDue_km.value is not None:
                if self.oilServiceEntry is None:
                    self.oilServiceEntry = Maintenance(self.vehicle, None, None, MaintenanceType.OIL_SERVICE, None, maintenanceStatus.oilServiceDue_km.value)
                    with self.session.begin_nested():
                        try:
                            self.session.add(self.oilServiceEntry)
                        except IntegrityError as err:
                            LOG.warning('Could not add inspection entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                    self.session.commit()
                elif self.oilServiceEntry.due_in_km is None:
                    with self.session.begin_nested():
                        self.oilServiceEntry.due_in_km = maintenanceStatus.oilServiceDue_km.value
                    self.session.commit()
                else:
                    if maintenanceStatus.oilServiceDue_km.value > self.oilServiceEntry.due_in_km:
                        with self.session.begin_nested():
                            self.oilServiceEntry.date = element.value
                            if maintenanceStatus.mileage_km.enabled and maintenanceStatus.mileage_km.value is not None:
                                self.oilServiceEntry.mileage = maintenanceStatus.mileage_km.value
                        self.session.commit()
                        LOG.info(f'Oil service for vehicle {self.vehicle.vin} done')
                        self.oilServiceEntry = Maintenance(self.vehicle, None, None, MaintenanceType.OIL_SERVICE, None,
                                                           maintenanceStatus.oilServiceDue_km.value)
                        with self.session.begin_nested():
                            try:
                                self.session.add(self.oilServiceEntry)
                            except IntegrityError as err:
                                LOG.warning('Could not add inspection entry to the database, this is usually due to an error in the WeConnect API (%s)', err)
                        self.session.commit()
                    else:
                        with self.session.begin_nested():
                            self.oilServiceEntry.due_in_km = maintenanceStatus.oilServiceDue_km.value
                        self.session.commit()

    def commit(self):
        self.session.commit()
