from datetime import timezone

from flask import Blueprint, render_template, current_app, abort, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField, StringField
from wtforms.fields.html5 import DateTimeField, IntegerField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional

from vwsfriend.model.trip import Trip
from vwsfriend.model.settings import Settings, UnitOfLength, UnitOfTemperature

from vwsfriend.util.location_util import locationFromLatLon

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
    id = HiddenField('id', validators=[DataRequired()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    startDate = DateTimeField('Start Date and Time (UTC)', validators=[Optional()])
    endDate = DateTimeField('End Date and Time (UTC)', validators=[Optional()])
    start_position_latitude = DecimalField('Start Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    start_position_longitude = DecimalField('Start Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    start_mileage_km = IntegerField('Start Mileage in km', validators=[Optional(), NumberRange(min=0)])
    destination_position_latitude = DecimalField('Destination Position Latitude', places=10, validators=[Optional(), NumberRange(min=-90, max=90)])
    destination_position_longitude = DecimalField('Destination Position Longitude', places=10, validators=[Optional(), NumberRange(min=-180, max=180)])
    end_mileage_km = IntegerField('End Mileage in km', validators=[Optional(), NumberRange(min=0)])
    save = SubmitField('Save changes')
    delete = SubmitField('Delete Trip')


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


@bp.route('/trips/edit', methods=['GET', 'POST'])
def tripEdit():
    id = request.args.get('id')

    trip = current_app.db.session.query(Trip).filter(Trip.id == id).first()

    if trip is None:
        abort(404, f"Trip with id {id} doesn't exist.")

    form = TripEditForm()

    if form.delete.data:
        flash(f'Successfully deleted trip {id}')
        with current_app.db.session.begin_nested():
            current_app.db.session.delete(trip)
        current_app.db.session.commit()
        return render_template('database/trip_edit.html', current_app=current_app, form=None)

    if form.validate_on_submit():
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
        flash(f'Successfully updated trip {id}')

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

    return render_template('database/trip_edit.html', current_app=current_app, form=form)
