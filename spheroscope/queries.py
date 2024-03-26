#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from multiprocessing import Pool

import _gdbm
from flask import (Blueprint, Response, current_app, g, jsonify, redirect,
                   render_template, request, session, url_for)
from pandas import concat, read_csv

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Query, get_patterns

bp = Blueprint('queries', __name__, url_prefix='/queries')


def run_query(query, cwb_id):

    # init corpus
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    current_app.logger.info("query: %s", query.name)
    query_ser = query.serialize()

    # get dump
    try:
        dump = corpus.query(
            cqp_query=query_ser['cqp'],
            context=corpus_config['query']['context'],
            context_break=corpus_config['query']['context_break'],
            corrections=query_ser['anchors']['corrections'],
            match_strategy=corpus_config['query']['match_strategy'],
            propagate_error=True
        )
    except _gdbm.error:
        current_app.logger.warning(f"cache conflict, re-running query {query.name}")
        return run_query(query, cwb_id)

    # invalid query
    if isinstance(dump, str):
        current_app.logger.error(query_ser['meta']['name'])
        current_app.logger.error(dump)
        return dump

    # valid query, but no matches
    if len(dump.df) == 0:
        current_app.logger.warning("no results for query: {query_ser['cqp']}")
        return

    # retreive concordance
    matches = dump.concordance(
        form='slots',
        p_show=dict(corpus_config['display'])['p_show'],
        s_show=dict(corpus_config['display'])['s_show'],
        cut_off=None,
        slots=query_ser['anchors']['slots']
    )

    # add name
    matches['query'] = query_ser['meta']['name']

    # translate anchor points in slot_START and slot_END for all slots
    for slot in query_ser['anchors']['slots']:
        df = format_slot(dump, query_ser, slot)
        matches = matches.join(df)

    return matches


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

    # run all queries
    nr_cpus = current_app.config['NR_CPUS']
    if len(queries) > 1:
        current_app.logger.info(f'running {len(queries)} queries using {nr_cpus} CPUs')

    with Pool(nr_cpus) as pool:
        matches = pool.starmap(run_query, [(query, cwb_id) for query in queries])

    matches_list = [m for m in matches if not isinstance(m, str) and len(m) > 0]

    # create output dataframe
    if len(matches_list) > 0:
        current_app.logger.info("concatenating")
        result = concat(matches_list).reset_index()
        result = result.set_index(['query', 'match', 'matchend'])
    else:
        current_app.logger.error('none of the queries returned matches')
        return

    # make sure missing cpos are indicated as -1 and columns are integer
    for c in result.columns:
        if c.endswith("_START") or c.endswith("_END"):
            result[c] = result[c].fillna(-1, downcast='infer')

    return result


def format_slot(dump, query, slot):

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

    return df


def add_gold(result, cwb_id, pattern, s_cwb, s_gold):
    """add gold annotation to result of run_queries() on a textual basis
    (disregarding actual match and matchend).
    ---

    """

    # result from queries.run_queries(): indexed by ['query', 'match', 'matchend']
    # result from patterns.hierarchical_query(): indexed by ['query', 'slot-query', 'match', 'matchend']
    result = result.reset_index()

    try:
        # get gold if possible
        gold = read_csv(
            os.path.join(current_app.instance_path + "/../" + "library/", cwb_id, "gold", "adjudicated.tsv"),
            sep="\t", index_col=0
        )
    except FileNotFoundError:
        current_app.logger.info("no gold data found")
        result['TP'] = None
    else:
        gold = gold.loc[gold['pattern'] == pattern].rename(
            {s_gold: s_cwb, 'annotation': 'TP'}, axis=1
        )
        # remove leading "t" in gold for BREXIT-2016-RAND
        if not result[s_cwb].iloc[0].startswith("t"):
            gold[s_cwb] = gold[s_cwb].apply(lambda x: x[1:])
        result = result.merge(gold[[s_cwb, "TP"]], on=s_cwb, how='left')

    result['TP'] = result['TP'].fillna('?')

    # reset index
    if 'slot-query' in result.columns:
        index_cols = ['query', 'slot-query', 'match', 'matchend']
    else:
        index_cols = ['query', 'match', 'matchend']

    return result.set_index(index_cols)


def evaluate(matches, tp_column='TP'):
    """evaluate result of add_gold(run_queries()) on a textual basis
    ---

    """

    matches[tp_column] = matches[tp_column].replace(True, 'TP').replace(False, 'FP')
    statistics = matches.groupby(['query', tp_column]).size().unstack(fill_value=0)
    statistics.columns.name = None
    if 'TP' not in statistics.columns:
        statistics['TP'] = 0
    if 'FP' not in statistics.columns:
        statistics['FP'] = 0
    if '?' not in statistics.columns:
        statistics['?'] = 0
    statistics['N'] = statistics.sum(axis=1)
    statistics['prec.'] = statistics['TP'] / (statistics['FP'] + statistics['TP'])

    return statistics[['N', 'TP', 'FP', '?', 'prec.']]


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
    newresult.columns = newresult.columns.str.split('_', n=2, expand=True)

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
    cwb_id = session['corpus']['resources']['cwb_id']

    # get query matches gracefully
    queries = Query.query.filter_by(cwb_handle=cwb_id).order_by(Query.name)
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

        cwb_id = session['corpus']['resources']['cwb_id']

        query = Query(
            cqp=request.form['query'],
            name=request.form['name'],
            pattern_id=request.form['pattern'],
            cwb_handle=cwb_id,
            slots=request.form['slots'].replace("None", "null"),
            corrections=request.form['corrections'].replace("None", "null"),
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
            cwb_handle=session['corpus']['resources']['cwb_id'],
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace("None", "null"),
            corrections=request.form['corrections'].replace("None", "null")
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
    s_cwb = session['corpus']['meta']['s_cwb']
    s_gold = session['corpus']['meta']['s_gold']

    # get corpus from settings
    cwb_id = session['corpus']['resources']['cwb_id']

    # get query matches gracefully
    query = Query.query.filter_by(id=id).first()
    matches = run_query(query, cwb_id)
    if isinstance(matches, str):
        return '<br/><br/><b>Encountered CQP Error:</b><br/><br/>' + matches
    if matches is None:
        return f'<br/><br/><b>query does not have any matches in corpus "{cwb_id}".</b>'

    # select display columns
    display_columns = [x for x in matches.columns if x not in ['context_id', 'context', 'contextend']]

    # run button @ /queries/<id>/update
    if request.method == 'POST':

        old_matches = matches

        # create new query for diffing
        new_query = Query(
            cqp=request.form['query'],
            name=request.form['name'],
            cwb_handle=cwb_id,
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace("None", "null"),
            corrections=request.form['corrections'].replace("None", "null"),
            user_id=g.user.id
        )

        # run new query upon change
        if new_query.cqp != query.cqp or new_query.slots != query.slots or new_query.corrections != query.corrections:
            # get new query matches gracefully
            new_matches = run_query(new_query, cwb_id)
            if isinstance(new_matches, str):
                return '<br/><br/><b>Encountered CQP Error:</b><br/><br/>' + new_matches
            if new_matches is None:
                return f'<br/><br/><b>query does not have any matches in corpus "{cwb_id}".</b>'

            # merge new matches to old ones
            matches = new_matches.reset_index().merge(
                old_matches.reset_index(), how='outer', indicator=True, on=['match', 'matchend'], validate="1:1"
            ).set_index(['match', 'matchend'])
            # NB: index will contain duplicates if match and matchend didn't change but anchors or slots did

        else:
            new_matches = old_matches

        # evaluate old and new matches
        current_app.logger.info("evaluating")
        old_matches = add_gold(old_matches, cwb_id, query.pattern_id, s_cwb, s_gold)
        old_matches_stats = old_matches.reset_index().drop_duplicates(subset=[s_cwb])[['TP']]
        old_matches_stats['query'] = 'saved version'

        new_matches = add_gold(new_matches, cwb_id, query.pattern_id, s_cwb, s_gold)
        new_matches_stats = new_matches.reset_index().drop_duplicates(subset=[s_cwb])[['TP']]
        new_matches_stats['query'] = 'this version'

        statistics = evaluate(concat([old_matches_stats, new_matches_stats]))

        # render result
        current_app.logger.info("rendering result table")
        concordance = patch_query_results(new_matches)
        # concordance = concordance.drop('query', axis=1)

        return render_template('queries/result_table.html',
                               concordance=concordance,
                               statistics=statistics.to_html(
                                   justify='left',
                                   classes=['table', 'is-striped', 'is-hoverable', 'is-narrow', 'sortable']
                               ))

    # download button @ /queries/
    return Response(
        matches[display_columns].to_csv(sep="\t"),
        mimetype='text/csv',
        headers={"Content-disposition":
                 f"attachment; filename=query-{id}-concordance.tsv"}
    )
