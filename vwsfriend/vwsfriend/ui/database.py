import os
from io import BytesIO
import subprocess  # nosec
from datetime import datetime, timezone

from sqlalchemy import and_

from flask import Blueprint, render_template, current_app, abort, request, flash, redirect, url_for, send_file
from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField, StringField, SelectField, FileField, DateTimeField, IntegerField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional

from weconnect.errors import RetrievalError

from vwsfriend.model.trip import Trip
from vwsfriend.model.charging_session import ACDC, ChargingSession
from vwsfriend.model.refuel_session import RefuelSession
from vwsfriend.model.vehicle import Vehicle
from vwsfriend.model.settings import Settings, UnitOfLength, UnitOfTemperature
from vwsfriend.model.journey import Journey

from vwsfriend.util.location_util import locationFromLatLon, addCharger

bp = Blueprint('database', __name__, url_prefix='/database')


class SettingsEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    unit_of_length = HiddenField('unit_of_length', validators=[Optional()])
    unit_of_temperature = HiddenField('unit_of_temperature', validators=[Optional()])
    grafana_url = StringField('URL where the Grafana installation is reachable', validators=[DataRequired()])
    vwsfriend_url = StringField('URL where the VWsFriend installation is reachable', validators=[DataRequired()])
    locale = HiddenField('locale', validators=[Optional()])
    save = SubmitField('Save changes')


class TripEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    startDate = DateTimeField('Start Date and Time (UTC)', validators=[DataRequired()])
    endDate = DateTimeField('End Date and Time (UTC)', validators=[DataRequired()])
    start_position_latitude = DecimalField('Start Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    start_position_longitude = DecimalField('Start Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    start_mileage_km = IntegerField('Start Mileage in km', validators=[Optional(), NumberRange(min=0)])
    destination_position_latitude = DecimalField('Destination Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    destination_position_longitude = DecimalField('Destination Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    end_mileage_km = IntegerField('End Mileage in km', validators=[Optional(), NumberRange(min=0)])
    save = SubmitField('Save changes')
    add = SubmitField('Add Trip')
    delete = SubmitField('Delete Trip')


class ChargingSessionEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    connected = DateTimeField('Plug Connection Date and Time (UTC)', validators=[Optional()])
    locked = DateTimeField('Plug Locked Date and Time (UTC)', validators=[Optional()])
    started = DateTimeField('Charging Start Date and Time (UTC)', validators=[DataRequired()])
    ended = DateTimeField('Charging End Date and Time (UTC)', validators=[Optional()])
    unlocked = DateTimeField('Plug Unlocked Date and Time (UTC)', validators=[Optional()])
    disconnected = DateTimeField('Plug Disconnect Date and Time (UTC)', validators=[Optional()])
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
    realCharged_kWh = DecimalField('Real kWh charged', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    realCost_ct = IntegerField('Real cost in cents', validators=[Optional(), NumberRange(min=0)])

    save = SubmitField('Save changes')
    add = SubmitField('Add Session')
    delete = SubmitField('Delete Session')


class RefuelSessionEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    date = DateTimeField('Date and Time (UTC)', validators=[Optional()])
    startSOC_pct = IntegerField('SoC at start', validators=[Optional(), NumberRange(min=0, max=100)])
    endSOC_pct = IntegerField('SoC at end', validators=[Optional(), NumberRange(min=0, max=100)])
    mileage_km = IntegerField('Mileage in km when charging', validators=[Optional(), NumberRange(min=0)])
    position_latitude = DecimalField('Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    position_longitude = DecimalField('Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    realRefueled_l = DecimalField('Real l refueled', places=4, validators=[Optional(), NumberRange(min=0, max=1000)])
    realCost_ct = IntegerField('Real cost in cents', validators=[Optional(), NumberRange(min=0)])

    save = SubmitField('Save changes')
    add = SubmitField('Add Session')
    delete = SubmitField('Delete Session')


class JourneyEditForm(FlaskForm):
    id = HiddenField('id', validators=[Optional()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    start = DateTimeField('Start date and Time (UTC)', validators=[DataRequired()])
    end = DateTimeField('End date and Time (UTC)', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])

    save = SubmitField('Save changes')
    add = SubmitField('Add journey')
    delete = SubmitField('Delete journey')


class BackupRestoreForm(FlaskForm):
    file = FileField('Restore file', validators=[Optional()])

    restore = SubmitField('restore')
    backup = SubmitField('backup')


@bp.route('/settings/edit', methods=['GET', 'POST'])
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


@bp.route('/trips/edit', methods=['GET', 'POST'])  # noqa: C901
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
        flash(message='You need to provide a vin to add a trip', category='error')
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

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
                trip.start_location = locationFromLatLon(current_app.db.session, trip.start_position_latitude, trip.start_position_longitude)
            trip.destination_position_latitude = form.destination_position_latitude.data
            trip.destination_position_longitude = form.destination_position_longitude.data
            if trip.destination_position_latitude is not None and trip.destination_position_longitude is not None:
                trip.destination_location = locationFromLatLon(current_app.db.session, trip.destination_position_latitude, trip.destination_position_longitude)
            trip.start_mileage_km = form.start_mileage_km.data
            trip.end_mileage_km = form.end_mileage_km.data
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
            start_location = locationFromLatLon(current_app.db.session, start_position_latitude, start_position_longitude)
        else:
            start_location = None
        destination_position_latitude = form.destination_position_latitude.data
        destination_position_longitude = form.destination_position_longitude.data
        if destination_position_latitude is not None and destination_position_longitude is not None:
            destination_location = locationFromLatLon(current_app.db.session, destination_position_latitude, destination_position_longitude)
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
    else:
        form.vehicle_vin.data = vehicle.vin
        form.startDate.data = datetime.utcnow()
        form.endDate.data = datetime.utcnow()

        lasttrip = current_app.db.session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()
        if lasttrip is not None and lasttrip.end_mileage_km is not None:
            form.start_mileage_km.data = lasttrip.end_mileage_km
            form.end_mileage_km.data = lasttrip.end_mileage_km

    return render_template('database/trip_edit.html', current_app=current_app, form=form)


@bp.route('/charging-session/edit', methods=['GET', 'POST'])  # noqa: C901
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
        flash(message='You need to provide a vin to add a charging session', category='error')
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

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
            chargers = sorted(current_app.weConnect.getChargingStations(round(latitude, 4), round(longitude, 4), searchRadius=500).values(),
                              key=lambda station: station.distance.value)
            choices = [(None, 'unknown')]
            for charger in chargers:
                label = f'{charger.name.value} ({round(charger.distance.value)} m away)'
                choices.append((charger.id.value, label))
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
                chargingSession.location = locationFromLatLon(current_app.db.session, chargingSession.position_latitude, chargingSession.position_longitude)

            chargingSession.realCharged_kWh = form.realCharged_kWh.data
            chargingSession.realCost_ct = form.realCost_ct.data
            if form.charger_id.data is None or form.charger_id.data == 'None':
                chargingSession.charger = None
            else:
                chargerAdded = False
                for charger in chargers:
                    if charger.id.value == form.charger_id.data:
                        chargingSession.charger = addCharger(current_app.db.session, charger)
                        chargerAdded = True
                if not chargerAdded:
                    flash(message='Charger not valid anymore', category='error')

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
            chargingSession.location = locationFromLatLon(current_app.db.session, chargingSession.position_latitude, chargingSession.position_longitude)
        else:
            chargingSession.location = None
        if form.charger_id.data is None or form.charger_id.data == 'None':
            chargingSession.charger = None
        else:
            chargingSession.charger_id = form.charger_id.data
        chargingSession.realCharged_kWh = form.realCharged_kWh.data
        chargingSession.realCost_ct = form.realCost_ct.data

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
        form.realCharged_kWh.data = chargingSession.realCharged_kWh
        form.realCost_ct.data = chargingSession.realCost_ct
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


@bp.route('/refuel-session/edit', methods=['GET', 'POST'])  # noqa: C901
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
        flash(message='You need to provide a vin to add a refuel session', category='error')
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

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
                refuelSession.location = locationFromLatLon(current_app.db.session, refuelSession.position_latitude, refuelSession.position_longitude)
            refuelSession.realRefueled_l = form.realRefueled_l.data
            refuelSession.realCost_ct = form.realCost_ct.data

        current_app.db.session.commit()
        flash(message=f'Successfully updated refuel session {id}', category='info')

    elif refuelSession is None and form.add.data and form.validate_on_submit():
        date = form.date.data
        if date is not None:
            date = date.replace(tzinfo=timezone.utc, microsecond=0)

        latitude = form.position_latitude.data
        longitude = form.position_longitude.data
        if latitude is not None and longitude is not None:
            location = locationFromLatLon(current_app.db.session, latitude, longitude)
        else:
            location = None
        refuelSession = RefuelSession(vehicle=vehicle, date=date, startSOC_pct=form.startSOC_pct.data, endSOC_pct=form.endSOC_pct.data,
                                      mileage_km=form.mileage_km.data, position_latitude=latitude, position_longitude=longitude, location=location)
        refuelSession.realRefueled_l = form.realRefueled_l.data
        refuelSession.realCost_ct = form.realCost_ct.data

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
    else:
        form.vehicle_vin.data = vehicle.vin
        form.date.data = datetime.utcnow()

        lasttrip = current_app.db.session.query(Trip).filter(and_(Trip.vehicle == vehicle, Trip.startDate.isnot(None))).order_by(Trip.startDate.desc()).first()
        if lasttrip is not None and lasttrip.start_mileage_km is not None:
            form.mileage_km.data = lasttrip.start_mileage_km
        form.endSOC_pct.data = 100

    return render_template('database/refuel_session_edit.html', current_app=current_app, form=form)


@bp.route('/journey/edit', methods=['GET', 'POST'])  # noqa: C901
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
        flash(message='You need to provide a vin to add a journey', category='error')
    else:
        vehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
        if vehicle is None:
            flash(message=f'Vehicle with VIN {vin} does not exist', category='error')

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


@bp.route('/backup', methods=['GET', 'POST'])  # noqa: C901
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
