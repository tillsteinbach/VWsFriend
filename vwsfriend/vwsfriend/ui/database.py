import os
from io import BytesIO
import subprocess  # nosec
from datetime import datetime, timezone
import uuid
import re

from sqlalchemy import and_, func

from flask import Blueprint, render_template, current_app, abort, request, flash, redirect, url_for, send_file
from flask_login import login_required
from flask_wtf import FlaskForm
from vwsfriend.model.charger import Charger, Operator
from wtforms import SubmitField, HiddenField, StringField, SelectField, SelectMultipleField, FileField, DateTimeLocalField, IntegerField, DecimalField, \
    FormField, BooleanField, ValidationError
from wtforms.validators import DataRequired, NumberRange, Optional

from haversine import haversine, Unit

from weconnect.errors import RetrievalError

from vwsfriend.model.trip import Trip
from vwsfriend.model.charging_session import ACDC, ChargingSession
from vwsfriend.model.refuel_session import RefuelSession
from vwsfriend.model.vehicle import Vehicle
from vwsfriend.model.settings import Settings, UnitOfLength, UnitOfTemperature
from vwsfriend.model.journey import Journey
from vwsfriend.model.geofence import Geofence
from vwsfriend.model.location import Location
from vwsfriend.model.tag import Tag

from vwsfriend.util.location_util import amenityFromLatLon, addCharger, locationFromLatLonWithGeofence

bp = Blueprint('database', __name__, url_prefix='/database')


class SettingsEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    unit_of_length = HiddenField('unit_of_length', validators=[Optional()])
    unit_of_temperature = HiddenField('unit_of_temperature', validators=[Optional()])
    grafana_url = StringField('URL where the Grafana installation is reachable', validators=[DataRequired()])
    vwsfriend_url = StringField('URL where the VWsFriend installation is reachable', validators=[DataRequired()])
    locale = HiddenField('locale', validators=[Optional()])
    save = SubmitField('Save changes')


class LocationEditForm(FlaskForm):
    id_field = HiddenField('id', validators=[Optional()])
    name_field = StringField('name', validators=[Optional()], filters=[lambda x: x or None])
    latitude = DecimalField('Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = DecimalField('Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    display_name = StringField('Display Name', validators=[Optional()], filters=[lambda x: x or None])
    amenity = StringField('Amenity', validators=[Optional()], filters=[lambda x: x or None])
    house_number = StringField('House Number', validators=[Optional()], filters=[lambda x: x or None])
    road = StringField('Road', validators=[Optional()], filters=[lambda x: x or None])
    neighbourhood = StringField('Neighbourhood', validators=[Optional()], filters=[lambda x: x or None])
    city = StringField('City', validators=[Optional()], filters=[lambda x: x or None])
    postcode = StringField('Postcode', validators=[Optional()], filters=[lambda x: x or None])
    county = StringField('County', validators=[Optional()], filters=[lambda x: x or None])
    country = StringField('Country', validators=[Optional()], filters=[lambda x: x or None])
    state = StringField('State', validators=[Optional()], filters=[lambda x: x or None])
    state_district = StringField('State district', validators=[Optional()], filters=[lambda x: x or None])

    save = SubmitField('Save location')
    add = SubmitField('Add location')
    delete = SubmitField('Delete location')


class GeofenceEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    name = StringField('name', validators=[DataRequired()])
    latitude = DecimalField('Position Latitude', places=10, validators=[DataRequired(), NumberRange(min=-90, max=90)])
    longitude = DecimalField('Position Longitude', places=10, validators=[DataRequired(), NumberRange(min=-180, max=180)])
    radius = DecimalField('Radius in meters', places=0, validators=[DataRequired(), NumberRange(min=1, max=1000)])
    location = FormField(LocationEditForm, "Location")
    charger_id = SelectField("Charger", validators=[Optional()])

    save = SubmitField('Save geofence')
    add = SubmitField('Add geofence')
    delete = SubmitField('Delete geofence')


class TripEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    startDate = DateTimeLocalField('Start Date and Time (UTC)', validators=[DataRequired()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                   render_kw={"step": "1"})
    endDate = DateTimeLocalField('End Date and Time (UTC)', validators=[DataRequired()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                 render_kw={"step": "1"})
    start_position_latitude = DecimalField('Start Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    start_position_longitude = DecimalField('Start Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    start_mileage_km = IntegerField('Start Mileage in km', validators=[Optional(), NumberRange(min=0)])
    destination_position_latitude = DecimalField('Destination Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    destination_position_longitude = DecimalField('Destination Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    end_mileage_km = IntegerField('End Mileage in km', validators=[Optional(), NumberRange(min=0)])
    tags = SelectMultipleField('Tags', validators=[Optional()])
    save = SubmitField('Save changes')
    add = SubmitField('Add Trip')
    delete = SubmitField('Delete Trip')


class ChargingSessionEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    connected = DateTimeLocalField('Plug Connection Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                   render_kw={"step": "1"})
    locked = DateTimeLocalField('Plug Locked Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                render_kw={"step": "1"})
    started = DateTimeLocalField('Charging Start Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                 render_kw={"step": "1"})
    ended = DateTimeLocalField('Charging End Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                               render_kw={"step": "1"})
    unlocked = DateTimeLocalField('Plug Unlocked Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                  render_kw={"step": "1"})
    disconnected = DateTimeLocalField('Plug Disconnect Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                                      render_kw={"step": "1"})
    # maxChargeCurrentACSetting
    targetSOCSetting_pct = IntegerField('Target SoC Setting', validators=[Optional(), NumberRange(min=0, max=100)])
    maximumChargePower_kW = DecimalField('Maximum Power during session', places=4, validators=[Optional(), NumberRange(min=0)])
    acdc = SelectField("AC/DC", choices=ACDC.choices(), coerce=ACDC.coerce, validators=[DataRequired()])
    startSOC_pct = IntegerField('SoC at start', validators=[Optional(), NumberRange(min=0, max=100)])
    endSOC_pct = IntegerField('SoC at end', validators=[Optional(), NumberRange(min=0, max=100)])
    mileage_km = IntegerField('Mileage in km when charging', validators=[Optional(), NumberRange(min=0)])
    position_latitude = DecimalField('Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    position_longitude = DecimalField('Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    charger_id = SelectField("Charger", validators=[Optional()])
    meterStart_kWh = DecimalField('Meter start value (kWh)', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    meterEnd_kWh = DecimalField('Meter end value (kWh)', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    pricePerKwh_ct = DecimalField('Price per kWh', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    pricePerMinute_ct = DecimalField('Price per Minute', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    pricePerSession_ct = DecimalField('Price per Session', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    realCharged_kWh = DecimalField('Real kWh charged', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    realCost_ct = IntegerField('Real cost in cents', validators=[Optional(), NumberRange(min=0)])
    tags = SelectMultipleField('Tags', validators=[Optional()])

    save = SubmitField('Save changes')
    add = SubmitField('Add Session')
    delete = SubmitField('Delete Session')


class RefuelSessionEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    date = DateTimeLocalField('Date and Time (UTC)', validators=[Optional()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'], render_kw={"step": "1"})
    startSOC_pct = IntegerField('SoC at start', validators=[Optional(), NumberRange(min=0, max=100)])
    endSOC_pct = IntegerField('SoC at end', validators=[Optional(), NumberRange(min=0, max=100)])
    mileage_km = IntegerField('Mileage in km when charging', validators=[Optional(), NumberRange(min=0)])
    position_latitude = DecimalField('Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    position_longitude = DecimalField('Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    realRefueled_l = DecimalField('Real l refueled', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    realCost_ct = IntegerField('Real cost in cents', validators=[Optional(), NumberRange(min=0)])
    tags = SelectMultipleField('Tags', validators=[Optional()])

    save = SubmitField('Save changes')
    add = SubmitField('Add Session')
    delete = SubmitField('Delete Session')


class JourneyEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    start = DateTimeLocalField('Start date and Time (UTC)', validators=[DataRequired()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'],
                               render_kw={"step": "1"})
    end = DateTimeLocalField('End date and Time (UTC)', validators=[DataRequired()], format=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'], render_kw={"step": "1"})
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    tags = SelectMultipleField('Tags', validators=[Optional()])

    save = SubmitField('Save changes')
    add = SubmitField('Add journey')
    delete = SubmitField('Delete journey')


class ChargerEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    latitude = DecimalField('Position Latitude', places=10, validators=[DataRequired(), NumberRange(min=-90, max=90)])
    longitude = DecimalField('Position Longitude', places=10, validators=[DataRequired(), NumberRange(min=-180, max=180)])
    address = StringField('Address', validators=[Optional()], filters=[lambda x: x or None])
    max_power = DecimalField('Maximum Charge Power', places=1, validators=[Optional(), NumberRange(min=0, max=1000)])
    num_spots = IntegerField('Number of Spots', validators=[Optional(), NumberRange(min=1)])
    operator_id = SelectField("Operator", validators=[Optional()])

    save = SubmitField('Save charger')
    add = SubmitField('Add charger')
    delete = SubmitField('Delete charger')


class OperatorEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional()], filters=[lambda x: x or None])

    save = SubmitField('Save operator')
    add = SubmitField('Add operator')
    delete = SubmitField('Delete operator')


class TagEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    use_trips = BooleanField('Use for Trips', validators=[Optional()])
    use_charges = BooleanField('Use for Charging Sessions', validators=[Optional()])
    use_refueling = BooleanField('Use for Refueling Sessions', validators=[Optional()])
    use_journey = BooleanField('Use for Journeys', validators=[Optional()])

    save = SubmitField('Save tag')
    add = SubmitField('Add tag')
    delete = SubmitField('Delete tag')

    def validate_name(form, field):
        if len(field.data) > 10:
            raise ValidationError('Name must be not longer than 10 characters')
        if not re.match(r'^[A-Za-z0-9_-]+$', field.data):
            raise ValidationError('Name must only contain characters, numbers, - and _')


class BackupRestoreForm(FlaskForm):
    file = FileField('Restore file', validators=[Optional()])

    restore = SubmitField('restore')
    backup = SubmitField('backup')


@bp.route('/overview', methods=['GET'])
def overview():
    return render_template('database/overview.html', current_app=current_app)


@bp.route('/settings/edit', methods=['GET', 'POST'])
@login_required
def settingsEdit():
    settings = current_app.db.session.query(Settings).first()
    if settings is None:
        requestHost = request.headers.get('Host')
        grafanaHost = requestHost.replace("4000", "3000")
        settings = Settings(grafana_url=f'http://{grafanaHost}', vwsfriend_url=f'http://{requestHost}')

    form = SettingsEditForm()

    if form.validate_on_submit():
        with current_app.db.session.begin_nested():
            settings.unit_of_length = UnitOfLength(form.unit_of_length.data)
            settings.unit_of_temperature = UnitOfTemperature(form.unit_of_temperature.data)
            settings.grafana_url = form.grafana_url.data
            settings.vwsfriend_url = form.vwsfriend_url.data
            settings.locale = form.locale.data
            current_app.db.session.merge(settings)
        current_app.db.session.commit()
        return redirect(url_for('status.vehicles'))

    form.id.data = settings.id
    form.unit_of_length.data = settings.unit_of_length.value
    form.unit_of_temperature.data = settings.unit_of_temperature.value
    form.grafana_url.data = settings.grafana_url
    form.vwsfriend_url.data = settings.vwsfriend_url
    form.locale.data = settings.locale
    return render_template('database/settings_edit.html', current_app=current_app, form=form)


@bp.route('/trips/list', methods=['GET'])  # noqa: C901
@login_required
def tripList():
    trips = current_app.db.session.query(Trip).order_by(Trip.startDate.desc()).all()
    return render_template('database/trip_list.html', current_app=current_app, trips=trips or [])


@bp.route('/trips/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def tripEdit():  # noqa: C901
    id = None
    vin = None
    vehicle = None

    form = TripEditForm()

    if request.args is not None:
        id = request.args.get('id')
        vin = request.args.get('vin')
    if id is None and form.id.data is not None and form.id.data.isdigit():
        id = form.id.data
    trip = None

    if id is not None:
        trip = current_app.db.session.query(Trip).filter(Trip.id == id).first()

        if trip is None:
            abort(404, f"Trip with id {id} doesn't exist.")
    elif vin is None:
        vehicles = current_app.db.session.query(Vehicle).all()
        flash(message='You need to select a vehicle to add a trip', category='info')
        return render_template('database/select_vehicle.html', current_app=current_app, vehicles=vehicles)
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

    tags = current_app.db.session.query(Tag).filter((Tag.use_trips == True)).all()  # noqa: E712
    choices = []
    for tag in tags:
        label = tag.name
        if tag.description is not None:
            label += f' ({tag.description})'
        choices.append((tag.name, label))
    form.tags.choices = choices

    if trip is not None and form.delete.data:
        flash(f'Successfully deleted trip {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(trip)
        current_app.db.session.commit()
        return render_template('database/trip_edit.html', current_app=current_app, form=None)

    if trip is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            trip.startDate = form.startDate.data
            if trip.startDate is not None:
                trip.startDate = trip.startDate.replace(tzinfo=timezone.utc, microsecond=0)
            trip.endDate = form.endDate.data
            if trip.endDate is not None:
                trip.endDate = trip.endDate.replace(tzinfo=timezone.utc, microsecond=0)
            trip.start_position_latitude = form.start_position_latitude.data
            trip.start_position_longitude = form.start_position_longitude.data
            if trip.start_position_latitude is not None and trip.start_position_longitude is not None:
                trip.start_location = locationFromLatLonWithGeofence(current_app.db.session, trip.start_position_latitude, trip.start_position_longitude)
            trip.destination_position_latitude = form.destination_position_latitude.data
            trip.destination_position_longitude = form.destination_position_longitude.data
            if trip.destination_position_latitude is not None and trip.destination_position_longitude is not None:
                trip.destination_location = locationFromLatLonWithGeofence(current_app.db.session, trip.destination_position_latitude,
                                                                           trip.destination_position_longitude)
            trip.start_mileage_km = form.start_mileage_km.data
            trip.end_mileage_km = form.end_mileage_km.data

            tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
            trip.tags = tags

        current_app.db.session.commit()
        flash(message=f'Successfully updated trip {id}', category='info')

    elif trip is None and form.add.data and form.validate_on_submit():
        startDate = form.startDate.data
        if startDate is not None:
            startDate = startDate.replace(tzinfo=timezone.utc, microsecond=0)
        endDate = form.endDate.data
        if endDate is not None:
            endDate = endDate.replace(tzinfo=timezone.utc, microsecond=0)
        start_position_latitude = form.start_position_latitude.data
        start_position_longitude = form.start_position_longitude.data
        if start_position_latitude is not None and start_position_longitude is not None:
            start_location = locationFromLatLonWithGeofence(current_app.db.session, start_position_latitude, start_position_longitude)
        else:
            start_location = None
        destination_position_latitude = form.destination_position_latitude.data
        destination_position_longitude = form.destination_position_longitude.data
        if destination_position_latitude is not None and destination_position_longitude is not None:
            destination_location = locationFromLatLonWithGeofence(current_app.db.session, destination_position_latitude, destination_position_longitude)
        else:
            destination_location = None

        start_mileage_km = form.start_mileage_km.data
        end_mileage_km = form.end_mileage_km.data

        trip = Trip(vehicle, startDate, start_position_latitude, start_position_longitude, start_location, start_mileage_km)
        trip.endDate = endDate
        trip.destination_position_latitude = destination_position_latitude
        trip.destination_position_longitude = destination_position_longitude
        trip.destination_location = destination_location
        trip.end_mileage_km = end_mileage_km

        tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
        trip.tags = tags

        with current_app.db.session.begin_nested():
            current_app.db.session.add(trip)
        current_app.db.session.commit()
        current_app.db.session.refresh(trip)
        flash(message=f'Successfully added a new trip {trip.id}', category='info')

    if trip is not None:
        form.id.data = trip.id
        form.vehicle_vin.data = trip.vehicle_vin
        form.startDate.data = trip.startDate
        form.endDate.data = trip.endDate
        form.start_position_latitude.data = trip.start_position_latitude
        form.start_position_longitude.data = trip.start_position_longitude
        form.destination_position_latitude.data = trip.destination_position_latitude
        form.destination_position_longitude.data = trip.destination_position_longitude
        form.start_mileage_km.data = trip.start_mileage_km
        form.end_mileage_km.data = trip.end_mileage_km
        selected = []
        for tag in trip.tags:
            selected.append(tag.name)
        form.tags.data = selected
    else:
        form.vehicle_vin.data = vehicle.vin
        form.startDate.data = datetime.utcnow()
        form.endDate.data = datetime.utcnow()

        lasttrip = current_app.db.session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()
        if lasttrip is not None and lasttrip.end_mileage_km is not None:
            form.start_mileage_km.data = lasttrip.end_mileage_km
            form.end_mileage_km.data = lasttrip.end_mileage_km

    return render_template('database/trip_edit.html', current_app=current_app, form=form)


@bp.route('/charging-session/list', methods=['GET'])  # noqa: C901
@login_required
def chargingSessionList():
    sessions = current_app.db.session.query(ChargingSession).order_by(ChargingSession.started.desc(), ChargingSession.locked.desc(),
                                                                      ChargingSession.connected.desc()).all()
    return render_template('database/charging_session_list.html', current_app=current_app, sessions=sessions or [])


@bp.route('/charging-session/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def chargingSessionEdit():  # noqa: C901
    id = None
    vin = None
    vehicle = None

    form = ChargingSessionEditForm()

    if request.args is not None:
        id = request.args.get('id')
        vin = request.args.get('vin')
    if id is None and form.id.data is not None and form.id.data.isdigit():
        id = form.id.data
    chargingSession = None

    if id is not None:
        chargingSession = current_app.db.session.query(ChargingSession).filter(ChargingSession.id == id).first()

        if chargingSession is None:
            abort(404, f"Charging session with id {id} doesn't exist.")

    elif vin is None:
        vehicles = current_app.db.session.query(Vehicle).all()
        flash(message='You need to select a vehicle to add a trip', category='info')
        return render_template('database/select_vehicle.html', current_app=current_app, vehicles=vehicles)
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

    tags = current_app.db.session.query(Tag).filter((Tag.use_charges == True)).all()  # noqa: E712
    choices = []
    for tag in tags:
        label = tag.name
        if tag.description is not None:
            label += f' ({tag.description})'
        choices.append((tag.name, label))
    form.tags.choices = choices

    try:
        if form.position_latitude.data is not None:
            latitude = form.position_latitude.data
        elif chargingSession is not None:
            latitude = chargingSession.position_latitude
        else:
            latitude = None

        if form.position_longitude.data is not None:
            longitude = form.position_longitude.data
        elif chargingSession is not None:
            longitude = chargingSession.position_longitude
        else:
            longitude = None

        if latitude is not None and longitude is not None:
            chargers = sorted(current_app.weConnect.getChargingStations(round(latitude, 4), round(longitude, 4), searchRadius=150).values(),
                              key=lambda station: station.distance.value)
            choices = [(None, 'unknown')]
            for charger in chargers:
                label = f'{charger.name.value}'
                if charger.chargingSpots.enabled and len(charger.chargingSpots) > 0:
                    label += f', {len(charger.chargingSpots)} spots'
                if charger.chargingPower.enabled and charger.chargingPower.value is not None and charger.chargingPower.value > 0:
                    label += f', max. {charger.chargingPower.value} kW'
                label += f' ({round(charger.distance.value)} m away)'
                choices.append((charger.id.value, label))

            customChargers = current_app.db.session.query(Charger).filter(Charger.custom).all()
            positionCar = (latitude, longitude)
            for charger in customChargers:
                if charger.latitude is not None and charger.longitude is not None:
                    positionCharger = (charger.latitude, charger.longitude)
                    distanceToCar = haversine(positionCar, positionCharger, unit=Unit.METERS)
                    if distanceToCar > 150:
                        continue
                else:
                    distanceToCar = 0
                label = f'{charger.name} (Custom, {round(distanceToCar)} m away))'
                choices.append((charger.id, label))

            form.charger_id.choices = choices
        else:
            form.charger_id.choices = [(None, 'You need to first save the position of the charging session')]
    except RetrievalError as e:
        flash(message=f'Cannot retrieve chargers: {e}', category='error')
        pass

    if chargingSession is not None and form.delete.data:
        flash(message=f'Successfully deleted charging session {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(chargingSession)
        current_app.db.session.commit()
        return render_template('database/charging_session_edit.html', current_app=current_app, form=None)

    if chargingSession is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            chargingSession.connected = form.connected.data
            if chargingSession.connected is not None:
                chargingSession.connected = chargingSession.connected.replace(tzinfo=timezone.utc, microsecond=0)
            chargingSession.locked = form.locked.data
            if chargingSession.locked is not None:
                chargingSession.locked = chargingSession.locked.replace(tzinfo=timezone.utc, microsecond=0)
            chargingSession.started = form.started.data
            if chargingSession.started is not None:
                chargingSession.started = chargingSession.started.replace(tzinfo=timezone.utc, microsecond=0)
            chargingSession.ended = form.ended.data
            if chargingSession.ended is not None:
                chargingSession.ended = chargingSession.ended.replace(tzinfo=timezone.utc, microsecond=0)
            chargingSession.unlocked = form.unlocked.data
            if chargingSession.unlocked is not None:
                chargingSession.unlocked = chargingSession.unlocked.replace(tzinfo=timezone.utc, microsecond=0)
            chargingSession.disconnected = form.disconnected.data
            if chargingSession.disconnected is not None:
                chargingSession.disconnected = chargingSession.disconnected.replace(tzinfo=timezone.utc, microsecond=0)
            chargingSession.targetSOCSetting_pct = form.targetSOCSetting_pct.data
            chargingSession.maximumChargePower_kW = form.maximumChargePower_kW.data
            chargingSession.acdc = form.acdc.data
            chargingSession.startSOC_pct = form.startSOC_pct.data
            chargingSession.endSOC_pct = form.endSOC_pct.data
            chargingSession.mileage_km = form.mileage_km.data
            chargingSession.position_latitude = form.position_latitude.data
            chargingSession.position_longitude = form.position_longitude.data
            if chargingSession.position_latitude is not None and chargingSession.position_longitude is not None:
                chargingSession.location = locationFromLatLonWithGeofence(current_app.db.session, chargingSession.position_latitude,
                                                                          chargingSession.position_longitude)
            chargingSession.meterStart_kWh = form.meterStart_kWh.data
            chargingSession.meterEnd_kWh = form.meterEnd_kWh.data
            chargingSession.pricePerKwh_ct = form.pricePerKwh_ct.data
            chargingSession.pricePerMinute_ct = form.pricePerMinute_ct.data
            chargingSession.pricePerSession_ct = form.pricePerSession_ct.data
            chargingSession.realCharged_kWh = form.realCharged_kWh.data
            chargingSession.realCost_ct = form.realCost_ct.data
            if form.charger_id.data is None or form.charger_id.data == 'None':
                chargingSession.charger = None
            else:
                chargerAdded = False
                if form.charger_id.data.startswith('custom_'):
                    charger = current_app.db.session.query(Charger).filter(Charger.id == form.charger_id.data).first()
                    if charger is None:
                        flash(message='Charger not valid anymore', category='error')
                    chargingSession.charger = charger
                else:
                    for charger in chargers:
                        if charger.id.value == form.charger_id.data:
                            chargingSession.charger = addCharger(current_app.db.session, charger)
                            chargerAdded = True
                    if not chargerAdded:
                        flash(message='Charger not valid anymore', category='error')

            tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
            chargingSession.tags = tags
        current_app.db.session.commit()
        flash(message=f'Successfully updated charging session {id}', category='error')

    elif chargingSession is None and form.add.data and form.validate_on_submit():
        chargingSession = ChargingSession(vehicle)

        chargingSession.connected = form.connected.data
        chargingSession.locked = form.locked.data
        chargingSession.started = form.started.data
        chargingSession.ended = form.ended.data
        chargingSession.unlocked = form.unlocked.data
        chargingSession.disconnected = form.disconnected.data
        chargingSession.targetSOCSetting_pct = form.targetSOCSetting_pct.data
        chargingSession.maximumChargePower_kW = form.maximumChargePower_kW.data
        chargingSession.acdc = form.acdc.data
        chargingSession.startSOC_pct = form.startSOC_pct.data
        chargingSession.endSOC_pct = form.endSOC_pct.data
        chargingSession.mileage_km = form.mileage_km.data
        chargingSession.position_latitude = form.position_latitude.data
        chargingSession.position_longitude = form.position_longitude.data
        if chargingSession.position_latitude is not None and chargingSession.position_longitude is not None:
            chargingSession.location = locationFromLatLonWithGeofence(current_app.db.session, chargingSession.position_latitude,
                                                                      chargingSession.position_longitude)
        else:
            chargingSession.location = None
        if form.charger_id.data is None or form.charger_id.data == 'None':
            chargingSession.charger = None
        else:
            chargerAdded = False
            if form.charger_id.data.startswith('custom_'):
                charger = current_app.db.session.query(Charger).filter(Charger.id == form.charger_id.data).first()
                if charger is None:
                    flash(message='Charger not valid anymore', category='error')
                chargingSession.charger = charger
            else:
                for charger in chargers:
                    if charger.id.value == form.charger_id.data:
                        chargingSession.charger = addCharger(current_app.db.session, charger)
                        chargerAdded = True
                if not chargerAdded:
                    flash(message='Charger not valid anymore', category='error')
        chargingSession.meterStart_kWh = form.meterStart_kWh.data
        chargingSession.meterEnd_kWh = form.meterEnd_kWh.data
        chargingSession.pricePerKwh_ct = form.pricePerKwh_ct.data
        chargingSession.pricePerMinute_ct = form.pricePerMinute_ct.data
        chargingSession.pricePerSession_ct = form.pricePerSession_ct.data
        chargingSession.realCharged_kWh = form.realCharged_kWh.data
        chargingSession.realCost_ct = form.realCost_ct.data

        tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
        chargingSession.tags = tags

        with current_app.db.session.begin_nested():
            current_app.db.session.add(chargingSession)
        current_app.db.session.commit()
        current_app.db.session.refresh(chargingSession)
        flash(message=f'Successfully added a new charging session {chargingSession.id}', category='info')

    if chargingSession is not None:
        form.id.data = chargingSession.id
        form.vehicle_vin.data = chargingSession.vehicle_vin
        form.connected.data = chargingSession.connected
        form.locked.data = chargingSession.locked
        form.started.data = chargingSession.started
        form.ended.data = chargingSession.ended
        form.unlocked.data = chargingSession.unlocked
        form.disconnected.data = chargingSession.disconnected
        form.targetSOCSetting_pct.data = chargingSession.targetSOCSetting_pct
        form.maximumChargePower_kW.data = chargingSession.maximumChargePower_kW
        form.acdc.data = chargingSession.acdc
        form.startSOC_pct.data = chargingSession.startSOC_pct
        form.endSOC_pct.data = chargingSession.endSOC_pct
        form.mileage_km.data = chargingSession.mileage_km
        form.position_latitude.data = chargingSession.position_latitude
        form.position_longitude.data = chargingSession.position_longitude

        form.charger_id.data = chargingSession.charger_id
        form.meterStart_kWh.data = chargingSession.meterStart_kWh
        form.meterEnd_kWh.data = chargingSession.meterEnd_kWh
        form.pricePerKwh_ct.data = chargingSession.pricePerKwh_ct
        form.pricePerMinute_ct.data = chargingSession.pricePerMinute_ct
        form.pricePerSession_ct.data = chargingSession.pricePerSession_ct
        form.realCharged_kWh.data = chargingSession.realCharged_kWh
        form.realCost_ct.data = chargingSession.realCost_ct

        selected = []
        for tag in chargingSession.tags:
            selected.append(tag.name)
        form.tags.data = selected
    else:
        form.vehicle_vin.data = vehicle.vin
        form.started.data = datetime.utcnow()
        form.ended.data = datetime.utcnow()

        lasttrip = current_app.db.session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()
        if lasttrip is not None and lasttrip.start_mileage_km is not None:
            form.mileage_km.data = lasttrip.start_mileage_km

        choices = [(None, 'You need to first save the location of the charging session')]
        form.charger_id.choices = choices

    return render_template('database/charging_session_edit.html', current_app=current_app, form=form)


@bp.route('/refuel-session/list', methods=['GET'])  # noqa: C901
@login_required
def refuelSessionList():
    sessions = current_app.db.session.query(RefuelSession).order_by(RefuelSession.date.desc()).all()
    return render_template('database/refuel_session_list.html', current_app=current_app, sessions=sessions or [])


@bp.route('/refuel-session/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def refuelSessionEdit():  # noqa: C901
    id = None
    vin = None
    vehicle = None

    form = RefuelSessionEditForm()

    if request.args is not None:
        id = request.args.get('id')
        vin = request.args.get('vin')
    if id is None and form.id.data is not None and form.id.data.isdigit():
        id = form.id.data
    refuelSession = None

    if id is not None:
        refuelSession = current_app.db.session.query(RefuelSession).filter(RefuelSession.id == id).first()

        if refuelSession is None:
            abort(404, f"Refuel session with id {id} doesn't exist.")

    elif vin is None:
        vehicles = current_app.db.session.query(Vehicle).all()
        flash(message='You need to select a vehicle to add a trip', category='info')
        return render_template('database/select_vehicle.html', current_app=current_app, vehicles=vehicles)
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

    tags = current_app.db.session.query(Tag).filter((Tag.use_refueling == True)).all()  # noqa: E712
    choices = []
    for tag in tags:
        label = tag.name
        if tag.description is not None:
            label += f' ({tag.description})'
        choices.append((tag.name, label))
    form.tags.choices = choices

    if refuelSession is not None and form.delete.data:
        flash(message=f'Successfully deleted refuel session {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(refuelSession)
        current_app.db.session.commit()
        return render_template('database/refuel_session_edit.html', current_app=current_app, form=None)

    if refuelSession is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            refuelSession.date = form.date.data
            if refuelSession.date is not None:
                refuelSession.date = refuelSession.date.replace(tzinfo=timezone.utc, microsecond=0)
            refuelSession.startSOC_pct = form.startSOC_pct.data
            refuelSession.endSOC_pct = form.endSOC_pct.data
            refuelSession.mileage_km = form.mileage_km.data
            refuelSession.position_latitude = form.position_latitude.data
            refuelSession.position_longitude = form.position_longitude.data
            if refuelSession.position_latitude is not None and refuelSession.position_longitude is not None:
                refuelSession.location = amenityFromLatLon(current_app.db.session, refuelSession.position_latitude, refuelSession.position_longitude, 150,
                                                           'fuel')
            refuelSession.realRefueled_l = form.realRefueled_l.data
            refuelSession.realCost_ct = form.realCost_ct.data

            tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
            refuelSession.tags = tags

        current_app.db.session.commit()
        flash(message=f'Successfully updated refuel session {id}', category='info')

    elif refuelSession is None and form.add.data and form.validate_on_submit():
        date = form.date.data
        if date is not None:
            date = date.replace(tzinfo=timezone.utc, microsecond=0)

        latitude = form.position_latitude.data
        longitude = form.position_longitude.data
        if latitude is not None and longitude is not None:
            location = amenityFromLatLon(current_app.db.session, latitude, longitude, 150, 'fuel')
        else:
            location = None
        refuelSession = RefuelSession(vehicle=vehicle, date=date, startSOC_pct=form.startSOC_pct.data, endSOC_pct=form.endSOC_pct.data,
                                      mileage_km=form.mileage_km.data, position_latitude=latitude, position_longitude=longitude, location=location)
        refuelSession.realRefueled_l = form.realRefueled_l.data
        refuelSession.realCost_ct = form.realCost_ct.data

        tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
        refuelSession.tags = tags

        with current_app.db.session.begin_nested():
            current_app.db.session.add(refuelSession)
        current_app.db.session.commit()
        current_app.db.session.refresh(refuelSession)
        flash(message=f'Successfully added a new charging session {refuelSession.id}', category='info')

    if refuelSession is not None:
        form.id.data = refuelSession.id
        form.vehicle_vin.data = refuelSession.vehicle_vin
        form.date.data = refuelSession.date
        form.startSOC_pct.data = refuelSession.startSOC_pct
        form.endSOC_pct.data = refuelSession.endSOC_pct
        form.mileage_km.data = refuelSession.mileage_km
        form.position_latitude.data = refuelSession.position_latitude
        form.position_longitude.data = refuelSession.position_longitude
        form.realRefueled_l.data = refuelSession.realRefueled_l
        form.realCost_ct.data = refuelSession.realCost_ct

        selected = []
        for tag in refuelSession.tags:
            selected.append(tag.name)
        form.tags.data = selected
    else:
        form.vehicle_vin.data = vehicle.vin
        form.date.data = datetime.utcnow()

        lasttrip = current_app.db.session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()
        if lasttrip is not None and lasttrip.start_mileage_km is not None:
            form.mileage_km.data = lasttrip.start_mileage_km
        form.endSOC_pct.data = 100

    return render_template('database/refuel_session_edit.html', current_app=current_app, form=form)


@bp.route('/journey/list', methods=['GET'])  # noqa: C901
@login_required
def journeyList():
    journeys = current_app.db.session.query(Journey).order_by(Journey.start.desc()).all()
    return render_template('database/journey_list.html', current_app=current_app, journeys=journeys or [])


@bp.route('/journey/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def journeyEdit():  # noqa: C901
    id = None
    vin = None
    vehicle = None

    form = JourneyEditForm()

    if request.args is not None:
        id = request.args.get('id')
        vin = request.args.get('vin')
    if id is None and form.id.data is not None and form.id.data.isdigit():
        id = form.id.data
    journey = None

    if id is not None:
        journey = current_app.db.session.query(Journey).filter(Journey.id == id).first()

        if journey is None:
            abort(404, f"Journey with id {id} doesn't exist.")

    elif vin is None:
        vehicles = current_app.db.session.query(Vehicle).all()
        flash(message='You need to select a vehicle to add a trip', category='info')
        return render_template('database/select_vehicle.html', current_app=current_app, vehicles=vehicles)
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

    tags = current_app.db.session.query(Tag).filter((Tag.use_journey == True)).all()  # noqa: E712
    choices = []
    for tag in tags:
        label = tag.name
        if tag.description is not None:
            label += f' ({tag.description})'
        choices.append((tag.name, label))
    form.tags.choices = choices

    if journey is not None and form.delete.data:
        flash(message=f'Successfully deleted journey {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(journey)
        current_app.db.session.commit()
        return render_template('database/journey_edit.html', current_app=current_app, form=None)

    if journey is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            journey.start = form.start.data
            journey.end = form.end.data
            journey.title = form.title.data
            journey.description = form.description.data

            tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
            journey.tags = tags

        current_app.db.session.commit()
        flash(message=f'Successfully updated journey {id}', category='info')

    elif journey is None and form.add.data and form.validate_on_submit():
        start = form.start.data
        if start is not None:
            start = start.replace(tzinfo=timezone.utc, microsecond=0)
        end = form.end.data
        if end is not None:
            end = end.replace(tzinfo=timezone.utc, microsecond=0)

        journey = Journey(vehicle=vehicle, start=start, end=end, title=form.title.data)
        journey.description = form.description.data

        tags = current_app.db.session.query(Tag).filter(Tag.name.in_(form.tags.data)).all()
        journey.tags = tags

        with current_app.db.session.begin_nested():
            current_app.db.session.add(journey)
        current_app.db.session.commit()
        current_app.db.session.refresh(journey)
        flash(message=f'Successfully added a new journey {journey.id}', category='info')

    if journey is not None:
        form.id.data = journey.id
        form.vehicle_vin.data = journey.vehicle_vin
        form.start.data = journey.start
        form.end.data = journey.end
        form.title.data = journey.title
        form.description.data = journey.description

        selected = []
        for tag in journey.tags:
            selected.append(tag.name)
        form.tags.data = selected
    else:
        form.vehicle_vin.data = vehicle.vin
        if request.args is not None:
            tripstart = request.args.get('tripstart')
            if tripstart is not None:
                form.start.data = datetime.utcfromtimestamp(int(tripstart) / 1000)
            tripend = request.args.get('tripend')
            if tripend is not None:
                form.end.data = datetime.utcfromtimestamp(int(tripend) / 1000)

    return render_template('database/journey_edit.html', current_app=current_app, form=form)


@bp.route('/operator/list', methods=['GET'])  # noqa: C901
@login_required
def operatorList():
    operators = current_app.db.session.query(Operator).order_by(Operator.id.asc()).filter(Operator.custom).all()
    return render_template('database/operator_list.html', current_app=current_app, operators=operators or [])


@bp.route('/operator/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def operatorEdit():  # noqa: C901
    id = None

    form = OperatorEditForm()

    if request.args is not None:
        id = request.args.get('id')
    if id is None and form.id.data is not None and form.id.data.isdigit():
        id = form.id.data
    operator = None

    if id is not None:
        operator = current_app.db.session.query(Operator).filter(Operator.id == id).first()

        if operator is None:
            abort(404, f"Operator with id {id} doesn't exist.")
        elif operator.custom is False:
            flash(message=f"Operator with id {id} is not a custom created operator and cannot be changed.")

    if operator is not None and form.delete.data:
        flash(message=f'Successfully deleted operator {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(operator)
        current_app.db.session.commit()
        return render_template('database/operator_edit.html', current_app=current_app, form=None)

    if operator is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            operator.name = form.name.data
            operator.phone = form.phone.data

        current_app.db.session.commit()
        flash(message=f'Successfully updated operator {id}', category='info')

    elif operator is None and form.add.data and form.validate_on_submit():
        operator = Operator(id=None, name=form.name.data, phone=form.phone.data, custom=True)
        operator.id = f'custom_{str(uuid.uuid4())}'

        with current_app.db.session.begin_nested():
            current_app.db.session.add(operator)
        current_app.db.session.commit()
        current_app.db.session.refresh(operator)
        flash(message=f'Successfully added a new operator {operator.id}', category='info')

    if operator is not None:
        form.id.data = operator.id
        form.name.data = operator.name
        form.phone.data = operator.phone

    return render_template('database/operator_edit.html', current_app=current_app, form=form)


@bp.route('/tag/list', methods=['GET'])  # noqa: C901
@login_required
def tagList():
    tags = current_app.db.session.query(Tag).order_by(Tag.name.asc()).all()
    return render_template('database/tag_list.html', current_app=current_app, tags=tags or [])


@bp.route('/tag/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def tagEdit():  # noqa: C901
    name = None

    form = TagEditForm()

    if request.args is not None:
        name = request.args.get('name')
    tag = None

    if name is not None:
        tag = current_app.db.session.query(Tag).filter(Tag.name == name).first()

        if tag is None:
            abort(404, f"Tag {name} doesn't exist.")

    if tag is not None and form.delete.data:
        flash(message=f'Successfully deleted tag {name}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(tag)
        current_app.db.session.commit()
        return render_template('database/tag_edit.html', current_app=current_app, form=None)

    if tag is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            tag.name = form.name.data
            tag.description = form.description.data
            tag.use_trips = form.use_trips.data
            tag.use_charges = form.use_charges.data
            tag.use_refueling = form.use_refueling.data
            tag.use_journey = form.use_journey.data

        current_app.db.session.commit()
        flash(message=f'Successfully updated tag {name}', category='info')

    elif tag is None and form.add.data and form.validate_on_submit():
        tag = Tag(name=form.name.data, description=form.description.data)
        tag.use_trips = form.use_trips.data
        tag.use_charges = form.use_charges.data
        tag.use_refueling = form.use_refueling.data
        tag.use_journey = form.use_journey.data

        with current_app.db.session.begin_nested():
            current_app.db.session.add(tag)
        current_app.db.session.commit()
        current_app.db.session.refresh(tag)
        flash(message=f'Successfully added a new tag {tag.name}', category='info')

    if tag is not None:
        form.name.data = tag.name
        form.description.data = tag.description
        form.use_trips.data = tag.use_trips
        form.use_charges.data = tag.use_charges
        form.use_refueling.data = tag.use_refueling
        form.use_journey.data = tag.use_journey

    return render_template('database/tag_edit.html', current_app=current_app, form=form)


@bp.route('/charger/list', methods=['GET'])  # noqa: C901
@login_required
def chargerList():
    chargers = current_app.db.session.query(Charger).order_by(Charger.id.asc()).filter(Charger.custom).all()
    return render_template('database/charger_list.html', current_app=current_app, chargers=chargers or [])


@bp.route('/charger/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def chargerEdit():  # noqa: C901
    id = None

    form = ChargerEditForm()

    if request.args is not None:
        id = request.args.get('id')
    if id is None and form.id.data is not None and len(form.id.data) > 0:
        id = form.id.data
    charger = None

    if id is not None:
        charger = current_app.db.session.query(Charger).filter(Charger.id == id).first()

        if charger is None:
            abort(404, f"Charger with id {id} doesn't exist.")
        elif charger.custom is False:
            flash(message=f"Charger with id {id} is not a custom created charger and cannot be changed.")

    operators = current_app.db.session.query(Operator).all()
    choices = [(None, 'unknown')]
    for operator in operators:
        label = f'{operator.name}'
        choices.append((operator.id, label))
    form.operator_id.choices = choices

    if charger is not None and form.delete.data:
        flash(message=f'Successfully deleted charger {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(charger)
        current_app.db.session.commit()
        return render_template('database/charger_edit.html', current_app=current_app, form=None)

    if charger is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            charger.name = form.name.data
            charger.latitude = form.latitude.data
            charger.longitude = form.longitude.data
            charger.address = form.address.data
            charger.max_power = form.max_power.data
            charger.num_spots = form.num_spots.data
            if form.operator_id.data is None or form.operator_id.data == 'None':
                charger.operator = None
            else:
                operator = current_app.db.session.query(Operator).filter(Operator.id == form.operator_id.data).first()
                if operator is None:
                    flash(message='Operator not valid anymore', category='error')
                charger.operator = operator

        current_app.db.session.commit()
        flash(message=f'Successfully updated charger {id}', category='info')

    elif charger is None and form.add.data and form.validate_on_submit():
        charger = Charger(id=None, custom=True)
        charger.id = f'custom_{str(uuid.uuid4())}'

        charger.name = form.name.data
        charger.latitude = form.latitude.data
        charger.longitude = form.longitude.data
        charger.address = form.address.data
        charger.max_power = form.max_power.data
        charger.num_spots = form.num_spots.data
        charger.operator_id = form.operator_id.data
        if form.operator_id.data is None or form.operator_id.data == 'None':
            charger.operator = None
        else:
            operator = current_app.db.session.query(Operator).filter(Operator.id == form.operator_id.data).first()
            if operator is None:
                flash(message='Operator not valid anymore', category='error')
            charger.operator = operator

        with current_app.db.session.begin_nested():
            current_app.db.session.add(charger)
        current_app.db.session.commit()
        current_app.db.session.refresh(charger)
        flash(message=f'Successfully added a new charger {charger.id}', category='info')

    if charger is not None:
        form.id.data = charger.id
        form.name.data = charger.name
        form.latitude.data = charger.latitude
        form.longitude.data = charger.longitude
        form.address.data = charger.address
        form.max_power.data = charger.max_power
        form.num_spots.data = charger.num_spots
        form.operator_id.data = charger.operator_id

    return render_template('database/charger_edit.html', current_app=current_app, form=form)


@bp.route('/geofence/list', methods=['GET'])  # noqa: C901
@login_required
def geofenceList():
    geofences = current_app.db.session.query(Geofence).order_by(Geofence.id.asc()).all()
    return render_template('database/geofence_list.html', current_app=current_app, geofences=geofences or [])


@bp.route('/geofence/edit', methods=['GET', 'POST'])  # noqa: C901
@login_required
def geofenceEdit():  # noqa: C901
    id = None

    form = GeofenceEditForm()

    if request.args is not None:
        id = request.args.get('id')
    if id is None and form.id.data is not None and form.id.data.isdigit():
        id = form.id.data
    geofence = None

    if id is not None:
        geofence = current_app.db.session.query(Geofence).filter(Geofence.id == id).first()

        if geofence is None:
            abort(404, f"Geofence with id {id} doesn't exist.")

    if form.latitude.data is not None:
        latitude = form.latitude.data
    elif geofence is not None:
        latitude = geofence.latitude
    else:
        latitude = None

    if form.longitude.data is not None:
        longitude = form.longitude.data
    elif geofence is not None:
        longitude = geofence.longitude
    else:
        longitude = None

    if form.radius.data is not None:
        radius = form.radius.data
    elif geofence is not None:
        radius = geofence.radius
    else:
        radius = 0

    if latitude is not None and longitude is not None:
        choices = [(None, 'unknown')]
        try:
            chargers = sorted(current_app.weConnect.getChargingStations(round(latitude, 4), round(longitude, 4), searchRadius=round(150 + radius)).values(),
                              key=lambda station: station.distance.value)
            for charger in chargers:
                label = f'{charger.name.value} ({round(charger.distance.value)} m away)'
                choices.append((charger.id.value, label))
        except RetrievalError as e:
            flash(message=f'Cannot retrieve chargers: {e}', category='error')
            pass

        customChargers = current_app.db.session.query(Charger).filter(Charger.custom).all()
        positionCar = (latitude, longitude)
        for charger in customChargers:
            if charger.latitude is not None and charger.longitude is not None:
                positionCharger = (charger.latitude, charger.longitude)
                distanceToCar = haversine(positionCar, positionCharger, unit=Unit.METERS)
                if distanceToCar > (150 + radius):
                    continue
            else:
                distanceToCar = 0
            label = f'{charger.name} (Custom, {round(distanceToCar)} m away))'
            choices.append((charger.id, label))

        form.charger_id.choices = choices
    else:
        form.charger_id.choices = [(None, 'You need to first save the position of the geofence')]

    if geofence is not None and form.delete.data:
        flash(message=f'Successfully deleted geofence {id}', category='info')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(geofence)
        current_app.db.session.commit()
        return render_template('database/geofence_edit.html', current_app=current_app, form=None)

    if geofence is not None and form.save.data and form.validate_on_submit():
        with current_app.db.session.begin_nested():
            geofence.name = form.name.data
            geofence.latitude = form.latitude.data
            geofence.longitude = form.longitude.data
            geofence.radius = form.radius.data
            if form.charger_id.data is None or form.charger_id.data == 'None':
                geofence.charger = None
            else:
                chargerAdded = False
                if form.charger_id.data.startswith('custom_'):
                    charger = current_app.db.session.query(Charger).filter(Charger.id == form.charger_id.data).first()
                    if charger is None:
                        flash(message='Custom charger not valid anymore', category='error')
                    geofence.charger = charger
                else:
                    for charger in chargers:
                        if charger.id.value == form.charger_id.data:
                            geofence.charger = addCharger(current_app.db.session, charger)
                            chargerAdded = True
                    if not chargerAdded:
                        flash(message='Charger not valid anymore', category='error')
            if form.location:
                if geofence.location is None:
                    geofence.location = Location()
                    row = current_app.db.session.query(func.min(Location.osm_id).label("min_osm_id")).one()
                    geofence.location.osm_id = (row.min_osm_id - 1) if row.min_osm_id is not None and row.min_osm_id < 0 else -1
                    geofence.location.osm_type = 'VWsFriend custom'
                geofence.location.latitude = form.latitude.data
                geofence.location.longitude = form.longitude.data
                geofence.location.display_name = form.location.display_name.data
                geofence.location.name = form.name.data
                geofence.location.amenity = form.location.amenity.data
                geofence.location.house_number = form.location.house_number.data
                geofence.location.road = form.location.road.data
                geofence.location.neighbourhood = form.location.neighbourhood.data
                geofence.location.city = form.location.city.data
                geofence.location.postcode = form.location.postcode.data
                geofence.location.county = form.location.county.data
                geofence.location.country = form.location.country.data
                geofence.location.state = form.location.state.data
                geofence.location.state_district = form.location.state_district.data

        current_app.db.session.commit()
        flash(message=f'Successfully updated geofence {id}', category='info')

    elif geofence is None and form.add.data and form.validate_on_submit():
        geofence = Geofence(id=None)
        geofence.name = form.name.data
        geofence.latitude = form.latitude.data
        geofence.longitude = form.longitude.data
        geofence.radius = form.radius.data
        geofence.location = form.location.data
        if form.charger_id.data is None or form.charger_id.data == 'None':
            geofence.charger = None
        else:
            chargerAdded = False
            if form.charger_id.data.startswith('custom_'):
                charger = current_app.db.session.query(Charger).filter(Charger.id == form.charger_id.data).first()
                if charger is None:
                    flash(message='Custom charger not valid anymore', category='error')
                geofence.charger = charger
            else:
                for charger in chargers:
                    if charger.id.value == form.charger_id.data:
                        geofence.charger = addCharger(current_app.db.session, charger)
                        chargerAdded = True
                if not chargerAdded:
                    flash(message='Charger not valid anymore', category='error')
        if form.location.data:
            geofence.location = Location()
            row = current_app.db.session.query(func.min(Location.osm_id).label("min_osm_id")).one()
            geofence.location.osm_id = (row.min_osm_id - 1) if row.min_osm_id is not None and row.min_osm_id < 0 else -1
            geofence.location.osm_type = 'VWsFriend custom'
            geofence.latitude = form.latitude.data
            geofence.longitude = form.longitude.data
            geofence.location.display_name = form.location.display_name.data
            geofence.location.name = form.name.data
            geofence.location.amenity = form.location.amenity.data
            geofence.location.house_number = form.location.house_number.data
            geofence.location.road = form.location.road.data
            geofence.location.neighbourhood = form.location.neighbourhood.data
            geofence.location.city = form.location.city.data
            geofence.location.postcode = form.location.postcode.data
            geofence.location.county = form.location.county.data
            geofence.location.country = form.location.country.data
            geofence.location.state = form.location.state.data
            geofence.location.state_district = form.location.state_district.data

        with current_app.db.session.begin_nested():
            current_app.db.session.add(geofence)
        current_app.db.session.commit()
        current_app.db.session.refresh(geofence)
        flash(message=f'Successfully added a new geofence {geofence.id}', category='info')

    if geofence is not None:
        form.id.data = geofence.id
        form.name.data = geofence.name
        form.latitude.data = geofence.latitude
        form.longitude.data = geofence.longitude
        form.radius.data = geofence.radius
        form.charger_id.data = geofence.charger_id
        if geofence.location is not None:
            form.location.display_name.data = geofence.location.display_name
            form.location.amenity.data = geofence.location.amenity
            form.location.house_number.data = geofence.location.house_number
            form.location.road.data = geofence.location.road
            form.location.neighbourhood.data = geofence.location.neighbourhood
            form.location.city.data = geofence.location.city
            form.location.postcode.data = geofence.location.postcode
            form.location.county.data = geofence.location.county
            form.location.country.data = geofence.location.country
            form.location.state.data = geofence.location.state
            form.location.state_district.data = geofence.location.state_district

    return render_template('database/geofence_edit.html', current_app=current_app, form=form)


@bp.route('/backup', methods=['GET', 'POST'])  # noqa: C901
@login_required
def backup():  # noqa: C901
    form = BackupRestoreForm()

    if form.restore.data and form.validate_on_submit():
        if not form.file.data:
            flash('No file part')
        else:
            file = form.file.data
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
            elif file and file.filename.endswith('.vwsfrienddbbackup'):
                if current_app.configDir is None or not os.path.isdir(current_app.configDir):
                    flash('Config directory is not configured or does not exist')
                else:
                    if not os.path.isdir(current_app.configDir + '/provisioning'):
                        os.makedirs(current_app.configDir + '/provisioning')
                    form.file.data.save(current_app.configDir + '/provisioning/database.vwsfrienddbbackup')
                    flash('backup was uploaded, now restarting to apply the backup')
                    return redirect(url_for('restart'))
            else:
                flash('File needs to be a .vwsfrienddbbackup')
    elif form.backup.data:
        try:
            dburl = current_app.config['SQLALCHEMY_DATABASE_URI']
            process = subprocess.run(['pg_dump', '--compress', '9', '--format', 'c', dburl], stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # nosec

            if process.returncode != 0:
                return abort(500, f"pg_dump returned {process.returncode}: {process.stderr.decode('ascii')}")
            return send_file(BytesIO(process.stdout), mimetype='application/gzip', as_attachment=True,
                             download_name=f'{datetime.now().strftime("%Y%m%dT%H%M%S")}.vwsfrienddbbackup')
        except FileNotFoundError as e:
            return abort(500, f"pg_dump was not found, you have to install it in order to be able to make database backups: {e}")

    return render_template('database/backup.html', current_app=current_app, form=form)
