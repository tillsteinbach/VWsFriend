import re
from collections import namedtuple

from flask import Blueprint, render_template, current_app, abort, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, StringField, IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional, Length, Regexp, ValidationError

from weconnect.elements.range_status import RangeStatus

from vwsfriend.model.vehicle_settings import VehicleSettings
from vwsfriend.model.vehicle import Vehicle
from vwsfriend.agents.abrp.abrp_agent import ABRPAgent


bp = Blueprint('settings', __name__, url_prefix='/settings')


class VehicleSettingsForm(FlaskForm):
    primary_capacity = IntegerField('Primary Capacity', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_wltp_range = IntegerField('Primary WLTP range in km', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    secondary_capacity = IntegerField('Secondary Capacity', validators=[Optional(), NumberRange(min=1, max=500)], filters=[lambda x: x or None])
    secondary_wltp_range = IntegerField('Secondary WLTP Range', validators=[Optional(), NumberRange(min=1, max=1000)], filters=[lambda x: x or None])
    save = SubmitField('Save')


class ElectricVehicleSettingsForm(VehicleSettingsForm):
    primary_capacity = IntegerField('Usable Battery Capacity (net) in kWh', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_wltp_range = IntegerField('WLTP range in km', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    secondary_capacity = HiddenField('Secondary Capacity', validators=[Optional(), NumberRange(min=1, max=500)], filters=[lambda x: x or None])
    secondary_wltp_range = HiddenField('Secondary WLTP Range', validators=[Optional(), NumberRange(min=1, max=1000)], filters=[lambda x: x or None])
    save = SubmitField('Save')


class HybridVehicleSettingsForm(VehicleSettingsForm):
    primary_capacity = IntegerField('Gasoline tank size in liters', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_wltp_range = IntegerField('WLTP range in km gasoline only', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    secondary_capacity = IntegerField('Usable Battery Capacity (net) in kWh', validators=[Optional(), NumberRange(min=1, max=500)],
                                      filters=[lambda x: x or None])
    secondary_wltp_range = IntegerField('WLTP range in km electic only', validators=[Optional(), NumberRange(min=1, max=1000)], filters=[lambda x: x or None])
    save = SubmitField('Save')


class ABRPSettingsForm(FlaskForm):
    class Account(FlaskForm):
        account_name = StringField('Account Name', validators=[Optional(), Length(min=1, max=255)])
        account_token = StringField('User Token', validators=[Optional(), Regexp(regex=r'[0-9a-f\-]{100}', message='token format is not correct')])
        delete = SubmitField('Delete')

    AccountEntry = namedtuple('Account', ('account_name', 'account_token'))

    accounts = FieldList(FormField(Account, 'ABRP Account'), min_entries=0, max_entries=10)
    save = SubmitField('Save')
    addAccount = SubmitField(label='Add Account')

    def validate_accounts(form, field):
        for data in field.data:
            if len(data['account_name']) < 1:
                raise ValidationError('Account name must not be empty')
            if not re.match(r'[0-9a-f\-]{10,100}', data['account_token']):
                raise ValidationError('Token is no real ABRP user token')


ABRPSettingsEntry = namedtuple('ABRPSettings', ('accounts'))


@bp.route('/vehicle/<vin>', methods=['GET', 'POST'])
def vehicle(vin):
    if vin not in current_app.weConnect.vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    foundVehicle = current_app.weConnect.vehicles[vin]

    return render_template('settings/vehicle.html', vehicle=foundVehicle, connector=current_app.connector)


@bp.route('/vehicle/database/<vin>', methods=['GET', 'POST'])
def vehicleDBParameters(vin):
    if vin not in current_app.weConnect.vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    foundVehicle = current_app.weConnect.vehicles[vin]
    dbVehicle = current_app.session.query(Vehicle).filter(Vehicle.vin == vin).first()
    if dbVehicle.settings is None:
        dbVehicle.settings = VehicleSettings(vehicle=dbVehicle)
        current_app.session.commit()

    if dbVehicle.carType == RangeStatus.CarType.ELECTRIC:
        form = ElectricVehicleSettingsForm()
    elif dbVehicle.carType == RangeStatus.CarType.HYBRID:
        form = HybridVehicleSettingsForm()
    else:
        form = VehicleSettingsForm()

    if request.method == "GET":
        form.primary_capacity.data = dbVehicle.settings.primary_capacity
        form.primary_wltp_range.data = dbVehicle.settings.primary_wltp_range
        form.secondary_capacity.data = dbVehicle.settings.secondary_capacity
        form.secondary_wltp_range.data = dbVehicle.settings.secondary_wltp_range
    elif form.validate_on_submit():
        dbVehicle.settings.primary_capacity = form.primary_capacity.data
        dbVehicle.settings.primary_wltp_range = form.primary_wltp_range.data
        dbVehicle.settings.secondary_capacity = form.secondary_capacity.data
        dbVehicle.settings.secondary_wltp_range = form.secondary_wltp_range.data
        current_app.session.commit()

        return redirect(url_for("settings.vehicle", vin=vin))

    return render_template('settings/vehicledbparameters.html', vehicle=foundVehicle, form=form, connector=current_app.connector)


@bp.route('/vehicle/abrp/<vin>', methods=['GET', 'POST'])  # noqa: C901
def vehicleABRPSettings(vin):  # noqa: C901
    if vin not in current_app.weConnect.vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    foundVehicle = current_app.weConnect.vehicles[vin]
    agent = None
    for connectorAgent in current_app.connector.agents[vin]:
        if isinstance(connectorAgent, ABRPAgent):
            agent = connectorAgent
    if agent is None:
        abort(404, f"ABRP was not enabled for vehicle with VIN {vin}")

    tokens = agent.userTokens
    data = ABRPSettingsEntry([ABRPSettingsForm.AccountEntry(x[0], x[1]) for x in tokens])
    form = ABRPSettingsForm(obj=data)

    validate = True

    if form.addAccount.data:
        form.accounts.append_entry()
        validate = False
    else:
        keepList = list()
        for account in form.accounts.entries:
            if not account.delete.data:
                keepList.append(account.data)
            else:
                validate = False
        for _ in range(len(form.accounts.entries)):
            form.accounts.pop_entry()
        for keep in keepList:
            form.accounts.append_entry(keep)

    if validate and form.validate_on_submit():
        newTokens = list()
        for entry in form.accounts.entries:
            newTokens.append((entry.account_name.data, entry.account_token.data))
        agent.userTokens = newTokens
        return redirect(url_for("settings.vehicle", vin=vin))

    return render_template('settings/abrpsettings.html', vehicle=foundVehicle, form=form, connector=current_app.connector)
