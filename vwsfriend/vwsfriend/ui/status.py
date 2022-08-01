from io import BytesIO
from base64 import b64encode
import json
from flask import Blueprint, Response, render_template, current_app, abort, send_file, request, redirect, url_for
from flask_login import login_required

from vwsfriend.ui.cache import cache

bp = Blueprint('status', __name__, url_prefix='/status')


@bp.route('/vehicles', methods=['GET'])
@login_required
def vehicles():
    vehicles = current_app.weConnect.vehicles.values()
    return render_template('status/vehicles.html', vehicles=vehicles, current_app=current_app)


@bp.route('/vehicle/<string:vin>/', methods=['GET'])
@login_required
def vehicle(vin):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    return render_template('status/vehicle.html', vehicle=vehicles[vin], current_app=current_app)


@bp.route('/vehicles/<string:vin>-status.png', defaults={'conversion': None}, methods=['GET'])
@bp.route('/vehicles/<string:vin>-status.png<string:conversion>', methods=['GET'])
def vehicleStatusImg(vin, conversion, badge=False):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        if 'fallback' in request.args:
            return redirect(url_for('static', filename=request.args.get('fallback')))
        else:
            abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    pictures = vehicles[vin].pictures
    if 'status' not in pictures:
        if 'fallback' in request.args:
            return redirect(url_for('static', filename=request.args.get('fallback')))
        else:
            abort(404, "Status picture doesn't exist.")
    else:
        img_io = BytesIO()
        if badge:
            pictures['statusWithBadge'].value.save(img_io, 'PNG')
        else:
            pictures['status'].value.save(img_io, 'PNG')
        img_io.seek(0)
    if conversion == '.json':
        jsonMap = {}
        jsonMap['type'] = 'image/png'
        jsonMap['encoding'] = 'base64'
        jsonMap['data'] = b64encode(img_io.read()).decode()
        return Response(json.dumps(jsonMap), mimetype='application/json')
    else:
        return send_file(img_io, mimetype='image/png')


@bp.route('/vehicles/<string:vin>-status-badge.png', defaults={'conversion': None}, methods=['GET'])
@bp.route('/vehicles/<string:vin>-status-badge.png<string:conversion>', methods=['GET'])
def vehicleStatusBadgeImg(vin, conversion):
    return vehicleStatusImg(vin, conversion, badge=True)


@bp.route('/vehicles/<string:vin>-car.png', defaults={'conversion': None}, methods=['GET'])
@bp.route('/vehicles/<string:vin>-car.png<string:conversion>', methods=['GET'])
def vehicleImg(vin, conversion, badge=False):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        if 'fallback' in request.args:
            return redirect(url_for('static', filename=request.args.get('fallback')))
        else:
            abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    pictures = vehicles[vin].pictures
    if 'car' not in pictures:
        if 'fallback' in request.args:
            return redirect(url_for('static', filename=request.args.get('fallback')))
        else:
            abort(404, "Status picture doesn't exist.")
    else:
        img_io = BytesIO()
        if badge:
            pictures['carWithBadge'].value.save(img_io, 'PNG')
        else:
            pictures['car'].value.save(img_io, 'PNG')
        img_io.seek(0)
        if conversion == '.json':
            jsonMap = {}
            jsonMap['type'] = 'image/png'
            jsonMap['encoding'] = 'base64'
            jsonMap['data'] = b64encode(img_io.read()).decode()
            return Response(json.dumps(jsonMap), mimetype='application/json')
        else:
            return send_file(img_io, mimetype='image/png')


@bp.route('/vehicles/<string:vin>-car-badge.png', defaults={'conversion': None}, methods=['GET'])
@bp.route('/vehicles/<string:vin>-car-badge.png<string:conversion>', methods=['GET'])
def vehicleImgBadge(vin, conversion):
    return vehicleImg(vin, conversion, badge=True)


@bp.route('/vehicles/<string:vin>-status_or_car.png', defaults={'conversion': None}, methods=['GET'])
@bp.route('/vehicles/<string:vin>-status_or_car.png<string:conversion>', methods=['GET'])
def vehicleStatusOrImg(vin, conversion, badge=False):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        if 'fallback' in request.args:
            return redirect(url_for('static', filename=request.args.get('fallback')))
        else:
            abort(404, f"Vehicle with VIN {vin} doesn't exist.")

    if vehicles[vin].statusExists('access', 'accessStatus') \
            and vehicles[vin].domains['access']['accessStatus'].carCapturedTimestamp.enabled:
        return vehicleStatusImg(vin, conversion, badge)
    return vehicleImg(vin, conversion, badge)


@bp.route('/vehicles/<string:vin>-status_or_car-badge.png', defaults={'conversion': None}, methods=['GET'])
@bp.route('/vehicles/<string:vin>-status_or_car-badge.png<string:conversion>', methods=['GET'])
def vehicleStatusOrImgBadge(vin, conversion):
    return vehicleStatusOrImg(vin, conversion, badge=True)


@bp.route('/json', methods=['GET'])
@cache.cached(timeout=5)
@login_required
def jsonStatus():
    json = current_app.weConnect.toJSON()
    response = Response(json, mimetype="text/json")
    response.cache_control.max_age = 5
    response.cache_control.private = True
    response.cache_control.public = False
    return response
