#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from ccc.cwb import Corpus

from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g, session
)

from .auth import login_required
from .corpora import read_config, init_corpus
from .database import Macro

bp = Blueprint('macros', __name__, url_prefix='/macros')


def get_frequencies(cwb_id, macro):

    # get frequencies
    current_app.logger.info(
        'getting frequency info for macro'
    )
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    dump = corpus.query("/" + macro.name + "()")
    freq = dump.breakdown()
    return freq


def get_defined_macros(cwb_id):
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    cqp = corpus.start_cqp()
    defined_macros = cqp.Exec("show macro;").split("\n")
    cqp.__kill__()
    return defined_macros


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    macros = Macro.query.order_by(Macro.name).all()

    if 'corpus' in session:
        cwb_id = session['corpus']['resources']['cwb_id']
    else:
        cwb_id = None

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
    attributes = Corpus(cwb_id).attributes_available
    s_atts = list(
        attributes.name[([
            not b for b in attributes.annotation
        ]) & (attributes.att == 's-Att')].values
    )
    corpus = {
        'cwb_id': cwb_id,
        's_atts': s_atts
    }

    if request.method == 'POST':
        macro = Macro(
            user_id=g.user.id,
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
    attributes = Corpus(cwb_id).attributes_available
    s_atts = list(
        attributes.name[([
            not b for b in attributes.annotation
        ]) & (attributes.att == 's-Att')].values
    )
    corpus = {
        'cwb_id': cwb_id,
        's_atts': s_atts
    }

    if request.method == 'POST':
        macro = Macro(
            id=id,
            user_id=g.user.id,
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
    )

    return render_template(
        'macros/frequencies.html',
        frequencies=freq,
        macro=macro,
        cwb_id=cwb_id
    )
