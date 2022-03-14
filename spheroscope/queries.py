#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from flask import (Blueprint, Response, current_app, g, jsonify, redirect,
                   render_template, request, session, url_for)
from pandas import concat, read_csv

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Query, get_patterns

bp = Blueprint('queries', __name__, url_prefix='/queries')


def run_queries(queries, cwb_id):
    """collect matches of queries as dataframe.
    ---

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

    # run all queries
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
        if len(dump.df) == 0:
            continue

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

        # translate anchor points in slot_START and slot_END for all slots
        for slot in query['anchors']['slots']:

            df = dump.df.reset_index()
            df.index = dump.df.index

            # select relevant columns
            columns = query['anchors']['slots'][slot]
            columns = [columns] if isinstance(columns, int) else columns
            for c in columns:
                if c not in df.columns:
                    current_app.logger.warning(
                        'anchor point %s not defined in query "%s"' % (str(c), query['meta']['name'])
                    )
                    df[c] = -1
            df = df[columns]

            if df.shape[1] == 1:
                # only one column: start and end are the same
                df.columns = ["_".join([str(slot), 'START'])]
                df["_".join([str(slot), 'END'])] = df["_".join([str(slot), 'START'])]
            elif df.shape[1] == 2:
                # two columns (start and end)
                df.columns = ["_".join([str(slot), 'START']), "_".join([str(slot), 'END'])]

            # join slots to matches dataframe
            matches = matches.join(df)

        # append to result list
        matches_list.append(matches.reset_index())

    # create output dataframe
    if len(matches_list) > 0:
        current_app.logger.info("concatenating")
        result = concat(matches_list).set_index(['query', 'match', 'matchend'])
    else:
        result = None

    return result


def add_gold(result, cwb_id, pattern, s_cwb, s_gold):
    """add gold annotation to result of run_queries() on a textual basis
    (disregarding actual match and matchend).
    ---

    """

    # result should be indexed by ['query', 'match', 'matchend']
    result = result.reset_index()

    try:
        # get and pre-process gold
        gold = read_csv(
            os.path.join("library", cwb_id, "gold", "adjudicated.tsv"),
            sep="\t", index_col=0
        )
        gold = gold.loc[gold['pattern'] == pattern].rename(
            {s_gold: s_cwb, 'annotation': 'TP'}, axis=1
        )
    except FileNotFoundError:
        result['TP'] = None
    else:
        result = result.merge(gold[[s_cwb, "TP"]], on=s_cwb, how='left')

    if 'slot-query' in result.columns:
        index_cols = ['query', 'slot-query', 'match', 'matchend']
    else:
        index_cols = ['query', 'match', 'matchend']
    result = result.set_index(index_cols)
    result['TP'] = result['TP'].fillna('?')

    return result


def evaluate(matches, s, tp_column='TP'):
    """evaluate result of add_gold(run_queries()) on a textual basis
    ---

    """

    matches = matches.drop_duplicates(subset=[s])
    tps = matches[tp_column]

    # get TPs, FPs, precision
    N = len(tps)
    tps = tps.value_counts().to_dict()
    tps['TP'] = tps.pop(True, 0)
    tps['FP'] = tps.pop(False, 0)
    tps['N'] = N

    try:
        tps['prec'] = tps['TP'] / (tps['FP'] + tps['TP'])
    except ZeroDivisionError:
        tps['prec'] = '?'

    return tps


def patch_query_results(result):
    """transform column names in MultiIndex
    ---

    """
    result = result[[c for c in result.columns if not (c.endswith("_START") or c.endswith("_END"))]]

    newresult = result.rename(columns={
        "word": "whole_word",
        "word_x": "whole_word_x",
        "word_y": "whole_word_y",
        "lemma": "whole_lemma",
        "lemma_x": "whole_lemma_x",
        "lemma_y": "whole_lemma_y",
        "_merge": "merge"
    })
    newresult.columns = newresult.columns.str.split('_', 2, expand=True)

    return newresult


def create_subcorpus(df, slot):
    """transform one slot of result of run_queries() into a valid dump
    (empty dataframe multi-indexed by match and matchend)
    ---

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


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    """
    list all queries
    ---
    parameters:
      - name: pattern
        in: query
        required: False
        description: only list queries belonging to one pattern

    """
    pattern = request.args.get('pattern')
    queries = Query.query.order_by(Query.name)
    return render_template('queries/index.html',
                           queries=(queries.filter_by(pattern_id=pattern).all()
                                    if pattern else queries.all()))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """
    create a query
    ---
    parameters:
      - name: query
        in: query
      - name: name
        in: query
      - name: pattern
        in: query
      - name: slots
        in: query
      - name: corrections
        in: query

    """

    if request.method == 'POST':

        query = Query(
            cqp=request.form['query'],
            name=request.form['name'],
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace(
                "None", "null"
            ),
            corrections=request.form['corrections'].replace(
                "None", "null"
            ),
            user_id=g.user.id
        )
        try:
            query.write()
        except json.JSONDecodeError:
            return "wrong input format in JSON strings"

        return redirect(url_for('queries.index'))

    return render_template('queries/create.html',
                           patterns=get_patterns())


@bp.route('/<int(signed=True):id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """
    update a query
    ---
    parameters:
      - name: id
        in: path
        type: int
        required: true
        description: query id

    """

    query = Query.query.filter_by(id=id).first()

    if request.method == 'POST':
        query.delete()
        query = Query(
            id=id,
            user_id=g.user.id,
            cqp=request.form['query'],
            name=request.form['name'],
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace(
                "None", "null"
            ),
            corrections=request.form['corrections'].replace(
                "None", "null"
            )
        )
        try:
            query.write()
        except json.JSONDecodeError:
            return "wrong input format in JSON strings"

        return jsonify(success=True)

    return render_template('queries/update.html',
                           query=query,
                           patterns=get_patterns())


@bp.route('/<int(signed=True):id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    """
    delete a query
    ---
    parameters:
      - name: id
        in: path
        type: int
        required: true
        description: query id

    """

    query = Query.query.filter_by(id=id).first()
    query.delete()

    return redirect(url_for('queries.index'))


@bp.route('/<int(signed=True):id>/matches', methods=('GET', 'POST'))
@login_required
def matches(id):
    """
    run a query
    if POSTing: create diff between old and new matches
    ---
    parameters:
      - name: id
        in: path
        type: int
        required: true
        description: query id

    """

    # mapping of s-att that contains gold annotation
    s_cwb = 'tweet_id'
    s_gold = 'tweet'

    # get corpus from settings
    cwb_id = session['corpus']['resources']['cwb_id']

    # run the old query
    query = Query.query.filter_by(id=id).first()
    old_matches = run_queries([query], cwb_id)

    if old_matches is None:
        return 'query does not have any matches'

    # select columns
    display_columns = [x for x in old_matches.columns if x not in [
        'context_id', 'context', 'contextend'
    ]]

    # run button @ /queries/<id>/update
    if request.method == 'POST':

        # create new query for diffing
        newquery = Query(
            cqp=request.form['query'],
            name=request.form['name'],
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace(
                "None", "null"
            ),
            corrections=request.form['corrections'].replace(
                "None", "null"
            ),
            user_id=g.user.id
        )

        # get new matches and merge to old matches
        new_matches = run_queries([newquery], cwb_id)
        if new_matches is None:
            return 'new query does not have any matches'
        # index = ['query', 'match', 'matchend']
        matches = new_matches.reset_index().merge(
            old_matches.reset_index(), how='outer', indicator=True
        ).set_index(['query', 'match', 'matchend'])
        # NB: index will contain duplicates if match and matchend didn't change but anchors or slots did

        # add gold, evaluate
        matches = add_gold(matches, cwb_id, query.pattern_id, s_cwb, s_gold)
        tps = evaluate(matches, s_cwb)

        # render result
        result = patch_query_results(matches)

        # this is counter-productive for diffing, obviously ...
        # cut off
        # cut_off = min(int(request.args.get('cut_off', 1000)), len(result))
        # result = result.sample(cut_off)

        current_app.logger.info("rendering result table")
        return render_template('queries/result_table.html',
                               result=result,
                               tps=tps)

    # download button @ /queries/
    return Response(
        old_matches[display_columns].to_csv(),
        mimetype='text/csv',
        headers={"Content-disposition":
                 f"attachment; filename={id}-results.csv"}
    )
