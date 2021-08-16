from flask import Blueprint, render_template

bp = Blueprint('status', __name__, url_prefix='/status')


@bp.route('/vehicles', methods=['GET'])
def vehicles():
    return render_template('status/vehicles.html')
