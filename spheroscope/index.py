#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

from .auth import login_required

bp = Blueprint('index', __name__)


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    return render_template('index.html')
