from io import BytesIO
from flask import Blueprint, render_template, current_app, abort, request, flash
from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, StringField, IntegerField, SubmitField, HiddenField, DateTimeField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional, Length, Regexp, ValidationError

from vwsfriend.model.trip import Trip

bp = Blueprint('database', __name__, url_prefix='/database')

class TripEditForm(FlaskForm):
    id = HiddenField('id', validators=[DataRequired()])
    vehicle_vin = HiddenField('id', validators=[DataRequired()])
    startDate = DateTimeField('Start Date and Time', validators=[DataRequired()])
    endDate = DateTimeField('End Date and Time', validators=[DataRequired()])
    start_position_latitude = FloatField('Start Position Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    start_position_longitude = FloatField('Start Position Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    destination_position_latitude = FloatField('Destination Position Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    destination_position_longitude = FloatField('Destination Position Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
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
        return render_template('database/trip_edit.html', current_app=current_app, form=None)

    if form.validate_on_submit():
        trip.startDate = form.startDate.data
        trip.endDate = form.endDate.data
        trip.start_position_latitude = form.start_position_latitude.data
        trip.start_position_longitude = form.start_position_longitude.data
        trip.destination_position_latitude = form.destination_position_latitude.data
        trip.destination_position_longitude = form.destination_position_longitude.data

    form.id.data = trip.id
    form.vehicle_vin.data = trip.vehicle_vin
    form.startDate.data = trip.startDate
    form.endDate.data = trip.endDate
    form.start_position_latitude.data = trip.start_position_latitude
    form.start_position_longitude.data = trip.start_position_longitude
    form.destination_position_latitude.data = trip.destination_position_latitude
    form.destination_position_longitude.data = trip.destination_position_longitude

    return render_template('database/trip_edit.html', current_app=current_app, form=form)
