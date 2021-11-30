#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, flash, render_template, session

from .auth import login_required
from .corpora import read_config

bp = Blueprint('index', __name__)


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():

    if 'corpus' not in session:
        session['corpus'] = read_config()
        flash(f"activated corpus {session['corpus']['resources']['cwb_id']}")

    return render_template('index.html')
