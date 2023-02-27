import re
from collections import namedtuple
from io import BytesIO
from pyqrcode import pyqrcode

from sqlalchemy import text

from flask import Blueprint, render_template, current_app, abort, redirect, url_for, request, send_file, flash
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, StringField, IntegerField, SubmitField, HiddenField, SelectField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Optional, Length, Regexp, ValidationError

from weconnect.elements.range_status import RangeStatus

from vwsfriend.model.vehicle_settings import VehicleSettings
from vwsfriend.model.vehicle import Vehicle
from vwsfriend.agents.abrp.abrp_agent import ABRPAgent


bp = Blueprint('settings', __name__, url_prefix='/settings')


class VehicleSettingsForm(FlaskForm):
    primary_capacity = IntegerField('Primary Capacity', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_capacity_total = IntegerField('Primary Capacity Total', validators=[Optional(), NumberRange(min=1, max=500)], filters=[lambda x: x or None])
    primary_wltp_range = IntegerField('Primary WLTP range in km', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    secondary_capacity = IntegerField('Secondary Capacity', validators=[Optional(), NumberRange(min=1, max=500)], filters=[lambda x: x or None])
    secondary_capacity_total = IntegerField('Secondary Capacity Total', validators=[Optional(), NumberRange(min=1, max=500)], filters=[lambda x: x or None])
    secondary_wltp_range = IntegerField('Secondary WLTP Range', validators=[Optional(), NumberRange(min=1, max=1000)], filters=[lambda x: x or None])
    timezone = SelectField("Timezone", validators=[DataRequired()])
    sorting_order = IntegerField("Add number to define sorting order in list (lowest number first)", validators=[Optional()])
    hide = BooleanField("Hide vehicle", validators=[Optional()])
    save = SubmitField('Save')


class ElectricVehicleSettingsForm(VehicleSettingsForm):
    primary_capacity = IntegerField('Usable Battery Capacity (net) in kWh', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_capacity_total = IntegerField('Total Battery Capacity (gross) in kWh', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_wltp_range = IntegerField('WLTP range in km', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    secondary_capacity = HiddenField('Secondary Capacity', validators=[Optional(), NumberRange(min=1, max=500)], filters=[lambda x: x or None])
    secondary_capacity_total = HiddenField('Secondary Capacity Total', validators=[Optional()], filters=[lambda x: x or None])
    secondary_wltp_range = HiddenField('Secondary WLTP Range', validators=[Optional()], filters=[lambda x: x or None])
    save = SubmitField('Save')


class HybridVehicleSettingsForm(VehicleSettingsForm):
    primary_capacity = IntegerField('Gasoline tank size in liters', validators=[DataRequired(), NumberRange(min=1, max=500)])
    primary_capacity_total = HiddenField('Primary Capacity Total', validators=[Optional()], filters=[lambda x: x or None])
    primary_wltp_range = IntegerField('WLTP range in km gasoline only', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    secondary_capacity = IntegerField('Usable Battery Capacity (net) in kWh', validators=[DataRequired(), NumberRange(min=1, max=500)],
                                      filters=[lambda x: x or None])
    secondary_capacity_total = IntegerField('Total Battery Capacity (gross) in kWh', validators=[DataRequired(), NumberRange(min=1, max=500)],
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


class HomekitForm(FlaskForm):
    unpair = SubmitField('Unpair')


ABRPSettingsEntry = namedtuple('ABRPSettings', ('accounts'))


@bp.route('/vehicle/<vin>', methods=['GET', 'POST'])
@login_required
def vehicle(vin):
    if vin not in current_app.weConnect.vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    foundVehicle = current_app.weConnect.vehicles[vin]

    return render_template('settings/vehicle.html', vehicle=foundVehicle, current_app=current_app)


@bp.route('/vehicle/database/<vin>', methods=['GET', 'POST'])
@login_required
def vehicleDBParameters(vin):
    if vin not in current_app.weConnect.vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    foundVehicle = current_app.weConnect.vehicles[vin]
    dbVehicle = current_app.db.session.query(Vehicle).filter(Vehicle.vin == vin).first()
    if dbVehicle is None:
        abort(404, f"Vehicle with VIN {vin} doesn't exist in the database, please try to restart VWsFriend")
    if dbVehicle.settings is None:
        dbVehicle.settings = VehicleSettings(vehicle=dbVehicle)
        with current_app.db.session.begin_nested():
            current_app.db.session.add(dbVehicle.settings)
        current_app.db.session.commit()

    if dbVehicle.carType == RangeStatus.CarType.ELECTRIC:
        form = ElectricVehicleSettingsForm()
    elif dbVehicle.carType == RangeStatus.CarType.HYBRID:
        form = HybridVehicleSettingsForm()
    else:
        form = VehicleSettingsForm()

    choices = [(None, 'unknown')]
    if current_app.db.get_engine().dialect.name == 'postgresql':
        result = current_app.db.session.execute(text('SELECT name FROM pg_timezone_names'
                                                     ' WHERE name !~ \'posix\' AND name !~ \'Etc\''
                                                     ' AND name !~ \'SystemV\' ORDER BY name asc;'))
        for row in result:
            choices.append((row[0], row[0]))
    else:
        choices.append(('UTC', 'UTC'))
    form.timezone.choices = choices

    if request.method == "GET":
        form.primary_capacity.data = dbVehicle.settings.primary_capacity
        form.primary_capacity_total.data = dbVehicle.settings.primary_capacity_total
        form.primary_wltp_range.data = dbVehicle.settings.primary_wltp_range
        form.secondary_capacity.data = dbVehicle.settings.secondary_capacity
        form.secondary_capacity_total.data = dbVehicle.settings.secondary_capacity_total
        form.secondary_wltp_range.data = dbVehicle.settings.secondary_wltp_range
        form.timezone.data = dbVehicle.settings.timezone
        form.sorting_order.data = dbVehicle.settings.sorting_order
        form.hide.data = dbVehicle.settings.hide
    elif form.validate_on_submit():
        dbVehicle.settings.primary_capacity = form.primary_capacity.data
        dbVehicle.settings.primary_capacity_total = form.primary_capacity_total.data
        dbVehicle.settings.primary_wltp_range = form.primary_wltp_range.data
        dbVehicle.settings.secondary_capacity = form.secondary_capacity.data
        dbVehicle.settings.secondary_capacity_total = form.secondary_capacity_total.data
        dbVehicle.settings.secondary_wltp_range = form.secondary_wltp_range.data
        dbVehicle.settings.timezone = form.timezone.data
        dbVehicle.settings.sorting_order = form.sorting_order.data
        dbVehicle.settings.hide = form.hide.data
        current_app.db.session.commit()

        return redirect(url_for("settings.vehicle", vin=vin))

    return render_template('settings/vehicledbparameters.html', vehicle=foundVehicle, form=form, current_app=current_app)


@bp.route('/vehicle/abrp/<vin>', methods=['GET', 'POST'])  # noqa: C901
@login_required
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

    return render_template('settings/abrpsettings.html', vehicle=foundVehicle, form=form, current_app=current_app)


@bp.route('/homekit', methods=['GET', 'POST'])
@login_required
def homekit():
    if current_app.homekitDriver is None:
        abort(404, 'Homekit support was not enabled. Enabled it with --with-homekit')

    form = HomekitForm()

    if form.unpair.data:
        clients = list(current_app.homekitDriver.state.paired_clients.keys()).copy()
        for client in clients:
            import asyncio
            try:
                asyncio.get_event_loop()
            except RuntimeError as ex:
                if "There is no current event loop in thread" in str(ex):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            current_app.homekitDriver.unpair(client)
            current_app.homekitDriver.config_changed()
        flash('Unpaired the Homekit bridge. You can now pair again')

    return render_template('settings/homekit.html', form=form, connector=current_app.connector, current_app=current_app)


@bp.route('/homekit/homekit-qr.png', methods=['GET'])
@login_required
def homekitQR():
    if current_app.homekitDriver is None or current_app.homekitDriver.accessory is None:
        abort(404, "VWsFriend is running without Homekit support")
    xhm_uri = current_app.homekitDriver.accessory.xhm_uri()
    qrcode = pyqrcode.create(xhm_uri)
    img_io = BytesIO()
    qrcode.png(img_io, scale=12)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
