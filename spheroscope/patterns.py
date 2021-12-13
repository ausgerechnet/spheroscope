#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, render_template, request, session, current_app

from .auth import login_required
from .database import Pattern, Query
from .corpora import read_config, init_corpus

from pandas import Series, DataFrame, concat

bp = Blueprint('patterns', __name__, url_prefix='/patterns')


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    patterns = Pattern.query.filter(Pattern.id >= 0).order_by(Pattern.id).all()
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


@bp.route('/<int:id>/subquery', methods=('GET', 'POST'))
@login_required
def run_subquery(id):
    """
    run a queries for a slot
    ---

    input:
    id: base pattern id
    slot: name of the slot
    slot_pattern: id of pattern to fill slot

    output:
    slot.0
    slot.1
    """

    cwb_id = session['corpus']['resources']['cwb_id']
    base_queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    slot = request.args.get('slot')
    slot_pattern = request.args.get('slot_pattern')

    # run all queries belonging to base pattern
    dfs = list()
    for query in base_queries:

        query = query.serialize()
        current_app.logger.info("query: %s", query['meta']['name'])

        # load corpus
        corpus_config = read_config(cwb_id)
        corpus = init_corpus(corpus_config)

        # check corrections
        corrections_int = dict()
        for k, c in query['anchors']['corrections'].items():
            corrections_int[int(k)] = c

        # get dump
        dump = corpus.query(
            cqp_query=query['cqp'],
            context=corpus_config['query']['context'],
            context_break=corpus_config['query']['context_break'],
            corrections=corrections_int,
            match_strategy=corpus_config['query']['match_strategy']
        )

        # process slots
        try:
            columns = query['anchors']['slots'][slot]
        except KeyError:
            current_app.logger.error(
                "undefined slot in query %s" % query['meta']['name']
            )
        else:
            df = dump.df[columns]
            if isinstance(df, Series):
                df = DataFrame(df)
                df.columns = ['start']
            if df.shape[1] == 1:
                df.columns = ['start']
                df['end'] = df['start']
            elif df.shape[1] == 2:
                df.columns = ['start', 'end']

            dfs.append(df)

    # create subcorpus
    df = concat(dfs)
    df = df.reset_index(drop=True)
    df = df[df.start != -1]
    df = df.sort_values(by='start')
    df = df.drop_duplicates()
    df = df[df['start'] <= df['end']]
    df = df.set_index(['start', 'end'])
    df.index.name = ('match', 'matchend')
    name = "Pattern%dSlot%s" % (id, slot)

    # activate NQR
    corpus.activate_subcorpus(name, df)

    # run all queries belonging to slot pattern on subcorpus

    return jsonify(None)
