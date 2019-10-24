from flask import Blueprint, render_template

from spheroscope.auth import login_required

bp = Blueprint('index', __name__)


@bp.route('/', methods=('GET', 'POST'))
@login_required
def create():
    return render_template('index.html')
