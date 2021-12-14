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

    # process request parameters
    cwb_id = session['corpus']['resources']['cwb_id']
    base_queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    slot = request.args.get('slot')
    slot_pattern = request.args.get('slot_pattern')
    slot_queries = Query.query.filter_by(pattern_id=slot_pattern).all()

    # load corpus
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    # run all queries belonging to base pattern
    dfs = list()
    concs = list()
    for query in base_queries:

        current_app.logger.info("query: %s", query.name)
        query = query.serialize()

        # get dump
        dump = corpus.query(
            cqp_query=query['cqp'],
            context=corpus_config['query']['context'],
            context_break=corpus_config['query']['context_break'],
            corrections=query['anchors']['corrections'],
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

            # for subcorpus creation
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

            # for concordance
            concs.append(dump.concordance(
                form='slots',
                p_show=dict(corpus_config['display'])['p_show'],
                s_show=dict(corpus_config['display'])['s_show'],
                cut_off=None,
                slots=query['anchors']['slots']
            ))

    # create subcorpus
    df = concat(dfs)
    df = df.reset_index(drop=True)
    df = df[df.start != -1]
    df = df.sort_values(by='start')
    df = df.drop_duplicates()
    df['end'][df['start'] <= df['end']] = df['start'][df['start'] <= df['end']]
    df = df.rename(columns={'start': 'match', 'end': 'matchend'}).set_index(
        ['match', 'matchend']
    )
    name = "Pattern%dSlot%s" % (id, slot)

    # create full concordance
    conc = concat(concs).reset_index().set_index(
        dict(corpus_config['display'])['s_show'][0]
    )

    # activate NQR
    corpus.activate_subcorpus(name, df)

    # run all queries belonging to slot pattern on subcorpus
    concs = list()
    for query in slot_queries:

        current_app.logger.info(query.name)
        query = query.serialize()
        dump = corpus.query(
            cqp_query=query['cqp'],
            context=corpus_config['query']['context'],
            context_break=corpus_config['query']['context_break'],
            corrections=query['anchors']['corrections'],
            match_strategy=corpus_config['query']['match_strategy']
        )
        concs.append(dump.concordance(
            form='slots',
            p_show=dict(corpus_config['display'])['p_show'],
            s_show=dict(corpus_config['display'])['s_show'],
            cut_off=None,
            slots=query['anchors']['slots']
        ))

    # join
    conc_slot = concat(concs).reset_index()
    if len(conc_slot) > 0:
        d = conc_slot[
            ["_".join([s, p]) for p in corpus_config['display']['p_show']
             for s in query['anchors']['slots']] +
            dict(corpus_config['display'])['s_show']
        ]
        renames = dict([
            ["_".join([s, p]), "_".join([str(slot), s, p])]
            for p in corpus_config['display']['p_show']
            for s in query['anchors']['slots']
        ])
        d = d.rename(columns=renames).set_index(
            dict(corpus_config['display'])['s_show'][0]
        )
        result = conc.join(d)
    else:
        result = conc

    return result.to_html()
