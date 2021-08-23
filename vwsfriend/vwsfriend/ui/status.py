from io import BytesIO
from flask import Blueprint, render_template, current_app, abort, send_file

bp = Blueprint('status', __name__, url_prefix='/status')


@bp.route('/vehicles', methods=['GET'])
def vehicles():
    vehicles = current_app.weConnect.vehicles.values()
    return render_template('status/vehicles.html', vehicles=vehicles, connector=current_app.connector)


@bp.route('/vehicles/<string:vin>-status.png', methods=['GET'])
def vehicleStatusImg(vin):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    pictures = vehicles[vin].pictures
    if 'status' not in pictures:
        abort(404, "Status picture doesn't exist.")
    else:
        img_io = BytesIO()
        pictures['status'].value.save(img_io, 'PNG')
        img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@bp.route('/vehicles/<string:vin>-car.png', methods=['GET'])
def vehicleImg(vin):
    vehicles = current_app.weConnect.vehicles
    if vin not in vehicles:
        abort(404, f"Vehicle with VIN {vin} doesn't exist.")
    pictures = vehicles[vin].pictures
    if 'car' not in pictures:
        abort(404, "Status picture doesn't exist.")
    else:
        img_io = BytesIO()
        pictures['car'].value.save(img_io, 'PNG')
        img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
