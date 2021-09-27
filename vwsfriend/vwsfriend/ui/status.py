from io import BytesIO
from flask import Blueprint, render_template, current_app, abort, send_file

bp = Blueprint('status', __name__, url_prefix='/status')


@bp.route('/vehicles', methods=['GET'])
def vehicles():
    vehicles = current_app.weConnect.vehicles.values()
    return render_template('status/vehicles.html', vehicles=vehicles, current_app=current_app)


@bp.route('/vehicle/<string:vin>/', methods=['GET'])
def vehicle(vin):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    return render_template('status/vehicle.html', vehicle=vehicles[vin], current_app=current_app)


@bp.route('/vehicles/<string:vin>-status.png', methods=['GET'])
def vehicleStatusImg(vin, badge=False):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    pictures = vehicles[vin].pictures
    if 'status' not in pictures:
        abort(404, "Status picture doesn't exist.")
    else:
        img_io = BytesIO()
        if badge:
            pictures['statusWithBadge'].value.save(img_io, 'PNG')
        else:
            pictures['status'].value.save(img_io, 'PNG')
        img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@bp.route('/vehicles/<string:vin>-status-badge.png', methods=['GET'])
def vehicleStatusBadgeImg(vin):
    return vehicleStatusImg(vin, badge=True)


@bp.route('/vehicles/<string:vin>-car.png', methods=['GET'])
def vehicleImg(vin, badge=False):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    pictures = vehicles[vin].pictures
    if 'car' not in pictures:
        abort(404, "Status picture doesn't exist.")
    else:
        img_io = BytesIO()
        if badge:
            pictures['carWithBadge'].value.save(img_io, 'PNG')
        else:
            pictures['car'].value.save(img_io, 'PNG')
        img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@bp.route('/vehicles/<string:vin>-car-badge.png', methods=['GET'])
def vehicleImgBadge(vin):
    return vehicleImg(vin, badge=True)


@bp.route('/vehicles/<string:vin>-status_or_car.png', methods=['GET'])
def vehicleStatusOrImg(vin, badge=False):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    statuses = vehicles[vin].statuses
    if 'accessStatus' in statuses:
        return vehicleStatusImg(vin, badge)
    return vehicleImg(vin, badge)


@bp.route('/vehicles/<string:vin>-status_or_car-badge.png', methods=['GET'])
def vehicleStatusOrImgBadge(vin, badge=False):
    return vehicleStatusOrImg(vin, badge=True)
