from datetime import timezone

from flask import Blueprint, render_template, current_app, abort, request, flash
from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField
from wtforms.fields.html5 import DateTimeField, IntegerField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional

from vwsfriend.model.trip import Trip

from vwsfriend.util.location_util import locationFromLatLon

bp = Blueprint('database', __name__, url_prefix='/database')


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


@bp.route('/trips/edit', methods=['GET', 'POST'])
def vehicleDBParameters():
    id = request.args.get('id')

    trip = current_app.session.query(Trip).filter(Trip.id == id).first()

    if trip is None:
        abort(404, f"Trip with id {id} doesn't exist.")

    form = TripEditForm()

    if form.delete.data:
        flash(f'Successfully deleted trip {id}')
        with current_app.session.begin_nested():
            current_app.session.delete(trip)
        return render_template('database/trip_edit.html', current_app=current_app, form=None)

    if form.validate_on_submit():
        with current_app.session.begin_nested():
            trip.startDate = form.startDate.data
            if trip.startDate is not None:
                trip.startDate = trip.startDate.replace(tzinfo=timezone.utc, microsecond=0)
            trip.endDate = form.endDate.data
            if trip.endDate is not None:
                trip.endDate = trip.endDate.replace(tzinfo=timezone.utc, microsecond=0)
            trip.start_position_latitude = form.start_position_latitude.data
            trip.start_position_longitude = form.start_position_longitude.data
            if trip.start_position_latitude is not None and trip.start_position_longitude is not None:
                trip.start_location = locationFromLatLon(current_app.session, trip.start_position_latitude, trip.start_position_longitude)
            trip.destination_position_latitude = form.destination_position_latitude.data
            trip.destination_position_longitude = form.destination_position_longitude.data
            if trip.destination_position_latitude is not None and trip.destination_position_longitude is not None:
                trip.destination_location = locationFromLatLon(current_app.session, trip.destination_position_latitude, trip.destination_position_longitude)
            trip.start_mileage_km = form.start_mileage_km.data
            trip.end_mileage_km = form.end_mileage_km.data
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
