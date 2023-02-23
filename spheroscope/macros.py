#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import (Blueprint, current_app, g, redirect, render_template,
                   request, session, url_for)

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Macro

bp = Blueprint('macros', __name__, url_prefix='/macros')


def get_frequencies(cwb_id, macro):

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    current_app.logger.info('getting frequency info for macro')
    dump = corpus.query("/" + macro.name + "()", context=0)
    freq = dump.breakdown()

    return freq


def get_defined_macros(cwb_id):

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    defined_macros = corpus._macros_available()

    return defined_macros


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():

    if 'corpus' in session:
        cwb_id = session['corpus']['resources']['cwb_id']
        macros = Macro.query.filter_by(cwb_handle=cwb_id).order_by(Macro.name).all()
    else:
        cwb_id = None
        macros = Macro.query.order_by(Macro.name).all()

    corpus = {
        'macros': get_defined_macros(cwb_id),
        'cwb_id': cwb_id
    }
    return render_template('macros/index.html',
                           macros=macros,
                           corpus=corpus)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):

    macro = Macro.query.filter_by(id=id).first()
    macro.delete()
    return redirect(url_for('macros.index'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    # get corpus info (for s-atts)
    cwb_id = session['corpus']['resources']['cwb_id']
    corpus_config = session['corpus']
    corpus = init_corpus(corpus_config)
    attributes = corpus.attributes_available
    s_atts_none = list(
        attributes['attribute'][([not b for b in attributes.annotation]) & (attributes['type'] == 's-Att')].values
    )
    corpus = {
        'cwb_id': cwb_id,
        's_atts': s_atts_none
    }

    if request.method == 'POST':
        macro = Macro(
            user_id=g.user.id,
            cwb_handle=session['corpus']['resources']['cwb_id'],
            name=request.form['name'],
            macro=request.form['macro'],
            path=os.path.join(
                current_app.instance_path, cwb_id, 'macros',
                request.form['name'] + ".txt"
            )
        )

        macro.delete()
        macro.write()
        return redirect(url_for('macros.index'))

    return render_template("macros/create.html",
                           corpus=corpus)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    macro = Macro.query.filter_by(id=id).first()

    # get corpus info (for s-atts)
    cwb_id = session['corpus']['resources']['cwb_id']
    corpus_config = session['corpus']
    corpus = init_corpus(corpus_config)
    attributes = corpus.attributes_available
    s_atts_none = list(
        attributes['attribute'][([not b for b in attributes.annotation]) & (attributes['type'] == 's-Att')].values
    )
    corpus = {
        'cwb_id': cwb_id,
        's_atts': s_atts_none
    }

    if request.method == 'POST':
        macro = Macro(
            id=id,
            user_id=g.user.id,
            cwb_handle=session['corpus']['resources']['cwb_id'],
            name=request.form['name'],
            macro=request.form['macro'],
            path=macro.path
        )

        macro.delete()
        macro.write()
        return redirect(url_for('macros.index'))

    return render_template("macros/update.html",
                           macro=macro,
                           corpus=corpus)


@bp.route('/<int:id>/frequencies', methods=['GET'])
@login_required
def frequencies(id):

    cwb_id = session['corpus']['resources']['cwb_id']
    macro = Macro.query.filter_by(id=id).first()

    # get frequencies
    freq = get_frequencies(
        cwb_id,
        macro
    )[['freq']].head(1000)

    return render_template(
        'macros/frequencies.html',
        frequencies=freq,
        macro=macro,
        cwb_id=cwb_id
    )
