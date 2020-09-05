#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

from .auth import login_required
from .database import Pattern, Query

bp = Blueprint('patterns', __name__, url_prefix='/patterns')


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    patterns = Pattern.query.filter(Pattern.id >= -1).order_by(Pattern.id).all()
    preamble = Pattern.query.filter_by(id=-2).first().template
    return render_template('patterns/index.html',
                           patterns=patterns,
                           preamble=preamble)


@bp.route('/<int(signed=True):id>', methods=('GET', 'POST'))
@login_required
def pattern(id):

    pattern = Pattern.query.filter_by(id=id).first()
    pattern.queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    return render_template('patterns/pattern.html',
                           pattern=pattern)
