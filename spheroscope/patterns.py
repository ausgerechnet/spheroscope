#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import Blueprint, jsonify, render_template, request, session, current_app

from .auth import login_required
from .database import Pattern, Query
from .corpora import read_config, init_corpus

from pandas import Series, DataFrame, concat, read_csv

bp = Blueprint('patterns', __name__, url_prefix='/patterns')


def run_queries_(queries, cwb_id):
    """
    collect matches of all queries belonging to one pattern as dataframe

    query_name
    match
    matchend
    corpus_config['display']['p_show']: p-attribute realization sequences of context
    corpus_config['display']['s_show']: s-attribute realizations at match
    for each slot in query['anchors']['slots']:
      slot_START
      slot_END
      for each p-att:
        slot_p-att

    """

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    # run all queries belonging to a pattern
    matches_list = list()

    for query in queries:

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

        # retreive concordance
        matches = dump.concordance(
            form='slots',
            p_show=dict(corpus_config['display'])['p_show'],
            s_show=dict(corpus_config['display'])['s_show'],
            cut_off=None,
            slots=query['anchors']['slots']
        )

        # add name
        matches['query'] = query['meta']['name']

        # translate anchors points in slot_START and slot_END for all slots
        for slot in query['anchors']['slots']:
            columns = query['anchors']['slots'][slot]
            columns = [columns] if isinstance(columns, int) else columns
            df = dump.df[list(columns)].copy()
            if df.shape[1] == 1:
                df.columns = ["_".join([str(slot), 'START'])]
                df["_".join([str(slot), 'END'])] = df["_".join([str(slot), 'START'])]
            elif df.shape[1] == 2:
                df.columns = ["_".join([str(slot), 'START']),
                              "_".join([str(slot), 'END'])]
            matches = matches.join(df)

        matches_list.append(matches.reset_index())

    result = concat(matches_list).set_index(['query', 'match', 'matchend'])

    return result


def add_gold(result, cwb_id, pattern, s_cwb='tweet_id', s_gold='tweet'):

    try:
        gold = read_csv(
            os.path.join("library", cwb_id, "gold", "adjudicated.tsv"),
            sep="\t", index_col=0
        )
    except FileNotFoundError:
        result['TP'] = None
    else:

        # pre-process gold
        gold = gold.loc[
            gold['pattern'] == pattern
        ].rename(
            {s_gold: s_cwb, 'annotation': 'TP'}, axis=1
        )

        # join explicit TPs and FPs
        result = result.merge(gold[[s_cwb, "TP"]], on=s_cwb, how='left')

    return result


def evaluate(tps):
    """

    :param pd.Series tps: column with True / False annotations

    """

    # get TPs, FPs, precision
    N = len(tps)
    tps = tps.value_counts().to_dict()
    tps['TP'] = tps.pop(True, 0)
    tps['FP'] = tps.pop(False, 0)
    tps['N'] = N

    try:
        tps['prec'] = tps['TP'] / (tps['FP'] + tps['TP'])
    except ZeroDivisionError:
        tps['prec'] = 'nan'

    return tps


def run_queries(queries, cwb_id, slot):

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    # run all queries belonging to a pattern
    dfs = list()
    concs = list()

    for query in queries:

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
            conc = dump.concordance(
                form='slots',
                p_show=dict(corpus_config['display'])['p_show'],
                s_show=dict(corpus_config['display'])['s_show'],
                cut_off=None,
                slots=query['anchors']['slots']
            )
            concs.append(conc)

    # create subcorpus
    df = concat(dfs)
    df = df.reset_index(drop=True)
    df = df[df.start != -1]
    df = df.sort_values(by='start')
    df = df.drop_duplicates()
    df['end'][df['start'] > df['end']] = df['start'][df['start'] <= df['end']]
    df = df.rename(columns={'start': 'match', 'end': 'matchend'}).set_index(
        ['match', 'matchend']
    )

    # create full concordance
    conc = concat(concs).reset_index().set_index(
        dict(corpus_config['display'])['s_show'][0]
    )

    return df, conc


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


@bp.route('/<int(signed=True):id>/matches', methods=('GET', 'POST'))
@login_required
def matches(id):
    """retrieve matches of all queries belonging to one pattern"""

    cut_off = int(request.args.get('cut_off', 1000))

    cwb_id = session['corpus']['resources']['cwb_id']
    queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    matches = run_queries_(queries, cwb_id)
    matches = add_gold(matches, cwb_id, id)
    tps = evaluate(matches['TP'])
    matches = matches.sample(cut_off)

    return render_template('queries/result_table.html',
                           result=matches,
                           tps=tps)


@bp.route('/<int(signed=True):id>/subquery', methods=('GET', 'POST'))
@login_required
def run_subquery(id):
    """execute a hierarchical query: retrieve matches of all queries
    belonging to a _base_ pattern, then run all queries belonging to
    _slot_ pattern on one slot defined in the base pattern.
    ---

    parameters:
      - name: id
        in: path
        type: int
        required: true
        description: base pattern id
      - name: slot
        in: query
        type: int
        required: true
        description: name of the slot
      - name: slot_pattern
        in: query
        type: int
        description: id of pattern to fill slot

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
    name = "Pattern%dSlot%s" % (id, slot)
    df, conc = run_queries(base_queries, cwb_id, slot)

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
        result = conc.join(d, how='inner')
    else:
        result = conc

    # dummy
    tps = {'TP': "nan", 'FP': "nan", 'prec': "nan", 'rec': "nan"}

    return render_template('queries/result_table.html',
                           result=result,
                           tps=tps)
