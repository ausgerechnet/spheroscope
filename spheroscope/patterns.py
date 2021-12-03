#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, render_template

from .auth import login_required
from .database import Pattern, Query

bp = Blueprint('patterns', __name__, url_prefix='/patterns')


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    patterns = Pattern.query.filter(Pattern.id >= 0).order_by(Pattern.id).all()
    print(patterns)
    return render_template('patterns/index.html',
                           patterns=patterns)


@bp.route('/api')
@login_required
def patterns():
    patterns = Pattern.query.order_by(Pattern.id).all()
    # FIXME this conversion should go when the new database is in
    patterndict = [{
        "id": abs(p.id),
        "template": p.template,
        "explanation": p.explanation,
        "retired": p.id < 0
    } for p in patterns]
    return jsonify(patterndict)


@bp.route('/<int(signed=True):id>', methods=('GET', 'POST'))
@login_required
def pattern(id):
    pattern = Pattern.query.filter_by(id=id).first()
    pattern.queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    return render_template('patterns/pattern.html',
                           pattern=pattern)
