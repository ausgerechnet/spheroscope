#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from flask import (Blueprint, current_app, jsonify, render_template, request,
                   session)
from pandas import concat, read_csv

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Pattern, Query
from .queries import patch_query_results

bp = Blueprint('patterns', __name__, url_prefix='/patterns')


def run_queries(queries, cwb_id):
    """collect matches of all queries belonging to one pattern as
    dataframe.

    index:
    - <str> query_name: name of the query
    - <int> match: match position of query
    - <int> matchend: matchend position of query

    columns:
    - corpus_config['display']['p_show']: p-attribute realization sequences of context
    - corpus_config['display']['s_show']: s-attribute realizations at match
    - for each slot in query['anchors']['slots']:
       - slot_START: start position of slot
       - slot_END: end position of slot
       for each p-att:
         - slot_p-att: p-attribute realization sequence of slot

    """

    # init corpus
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

        # append to result list
        matches_list.append(matches.reset_index())

    # create output dataframe
    result = concat(matches_list).set_index(['query', 'match', 'matchend'])

    return result


def add_gold(result, cwb_id, pattern, s_cwb='tweet_id', s_gold='tweet'):
    """add gold annotation to result of run_queries()

    """
    try:
        gold = read_csv(
            os.path.join("library", cwb_id, "gold", "adjudicated.tsv"),
            sep="\t", index_col=0
        )
    except FileNotFoundError:
        result['TP'] = None
    else:
        # pre-process gold
        gold = gold.loc[gold['pattern'] == pattern].rename(
            {s_gold: s_cwb, 'annotation': 'TP'}, axis=1
        )
        # join explicit TPs and FPs
        result = result.reset_index()
        result = result.merge(gold[[s_cwb, "TP"]], on=s_cwb, how='left')
        result = result.set_index(['query', 'match', 'matchend'])

    return result


def evaluate(tps):
    """evaluate "TP" column of result of run_queries()

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


def create_subcorpus(df, slot):
    """transform one slot of result of run_queries() into a valid dump
    (empty dataframe multi-indexed by match and matchend)

    """

    # select appropriate columns
    column_start = "_".join([str(slot), "START"])
    column_end = "_".join([str(slot), "END"])
    dump = df.reset_index(drop=True)[[column_start, column_end]]

    # only take rows where there's a match, sort ascending and deduplicate
    dump = dump.fillna(-1, downcast='infer')
    dump = dump[dump[column_start] != -1]
    dump = dump.sort_values(by=column_start)
    dump = dump.drop_duplicates()

    # post-proc: behaviour when start > end: start = end
    dump[column_end][
        dump[column_start] > dump[column_end]
    ] = dump[column_start][
        dump[column_start] > dump[column_end]
    ]

    # rename, convert to int, set index
    dump = dump.rename(
        columns={column_start: 'match', column_end: 'matchend'}
    ).set_index(
        ['match', 'matchend']
    )

    return dump


def hierarchical_query(p1, slot, p2):
    """execute a hierarchical query: retrieve matches of all queries
    belonging to a _base_ pattern, then run all queries belonging to
    _slot_ pattern on one slot defined in the base pattern.
    ---

    :param int p1: base pattern number
    :param str slot: slot name
    :param int p2: slot pattern

    """

    # make sure slot is a string
    slot = str(slot)

    # process request parameters
    cwb_id = session['corpus']['resources']['cwb_id']
    base_queries = Query.query.filter_by(pattern_id=p1).order_by(Query.name).all()
    slot_pattern = p2
    slot_queries = Query.query.filter_by(pattern_id=slot_pattern).all()

    # run all queries belonging to base pattern
    matches = run_queries(base_queries, cwb_id)
    corpus_config = read_config(cwb_id)
    matches = matches.reset_index().set_index(
        dict(corpus_config['display'])['s_show'][0]
    )

    # activate NQR
    df_dump = create_subcorpus(matches, slot)
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    name = "Pattern%dSlot%s" % (p1, slot)
    corpus.activate_subcorpus(name, df_dump)

    # run all queries belonging to slot pattern on activated NQR
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
        conc = dump.concordance(
            form='slots',
            p_show=dict(corpus_config['display'])['p_show'],
            s_show=dict(corpus_config['display'])['s_show'],
            cut_off=None,
            slots=query['anchors']['slots']
        )
        conc['name'] = query['meta']['name']
        concs.append(conc)

    # post-process
    if len(concs) > 0:
        conc_slot = concat(concs)
        conc_slot = conc_slot.reset_index()
        d = conc_slot[
            ["_".join([s, p]) for p in corpus_config['display']['p_show']
             for s in query['anchors']['slots']] +
            dict(corpus_config['display'])['s_show']
        ]
        renames = dict([
            ("_".join([s, p]), ".".join([str(slot), "_".join([s, p])]))
            for p in corpus_config['display']['p_show']
            for s in query['anchors']['slots']
        ])
        d = d.rename(columns=renames).set_index(
            dict(corpus_config['display'])['s_show'][0]
        )
        result = matches.join(d, how='inner')
    else:
        result = None

    return result


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
    patterns = Pattern.query.all()
    pattern.queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    slotfinder = re.compile(r"\d+")
    pattern.slots = set(slotfinder.findall(pattern.template))
    return render_template('patterns/pattern.html',
                           pattern=pattern,
                           patterns=patterns)


@bp.route('/<int(signed=True):id>/matches', methods=('GET', 'POST'))
@login_required
def matches(id):
    """retrieve matches of all queries belonging to one pattern"""

    cwb_id = session['corpus']['resources']['cwb_id']
    queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    matches = run_queries(queries, cwb_id)

    matches = add_gold(matches, cwb_id, id)
    tps = evaluate(matches['TP'])

    # cut_off
    matches = matches.sample(int(request.args.get('cut_off', 100)))

    return render_template('queries/standalone_result_table.html',
                           result=patch_query_results(matches),
                           tps=tps)


@bp.route('/<int(signed=True):p1>/matches/subquery', methods=('GET', 'POST'))
@login_required
def subquery(p1):
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
      - name: p2
        in: query
        type: int
        description: id of pattern to fill slot

    """

    # process request parameters
    cwb_id = session['corpus']['resources']['cwb_id']
    slot = request.args.get('slot')
    p2 = request.args.get('p2')

    # get matches
    result = hierarchical_query(p1, slot, p2)

    # evaluate matches
    result = add_gold(result, cwb_id, slot)
    tps = evaluate(result['TP'])

    return render_template('queries/standalone_result_table.html',
                           result=patch_query_results(result),
                           tps=tps)
