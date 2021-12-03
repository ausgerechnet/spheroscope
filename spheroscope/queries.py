#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from collections import defaultdict


import click
from ccc.cqpy import run_query
from flask import (Blueprint, Response, current_app, g, jsonify, redirect,
                   render_template, request, session, url_for)
from flask.cli import with_appcontext
from pandas import DataFrame, read_csv

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Pattern, Query

bp = Blueprint('queries', __name__, url_prefix='/queries')


def query_corpus(query, cwb_id):
    """execute a query in a corpus. this function makes sure that the
    query is valid input as expected by cwb-ccc's cqpy.run_query

    :param dict query: query as dictionary
    :param str cwb_id: CWB registry ID of the corpus
    """

    # get corpus config
    corpus_config = read_config(cwb_id)

    # load query and display parameters
    query['query'] = dict(corpus_config['query'])
    query['display'] = dict(corpus_config['display'])

    # make sure anchors are int
    corrections_int = dict()
    for k, c in query['anchors']['corrections'].items():
        corrections_int[int(k)] = c
    query['anchors']['corrections'] = corrections_int
    query['anchors']['slots']['match..matchend'] = ('match', 'matchend')

    # init corpus
    corpus = init_corpus(corpus_config)

    # run query
    current_app.logger.info('running query')

    lines = run_query(corpus, query)
    # TODO error handling
    # TODO take care of p_slots, p_text

    return lines


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    pattern = request.args.get('pattern')
    queries = Query.query.order_by(Query.name)
    return render_template('queries/index.html',
                           queries=(queries.filter_by(pattern_id=pattern).all() if pattern else queries.all()))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    # get corpus info (path)
    cwb_id = session['corpus']['resources']['cwb_id']

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
            path=os.path.join(
                current_app.instance_path, cwb_id, 'queries',
                request.form['name'] + ".cqpy"
            ),
            user_id=g.user.id
        )
        query.write()

        return redirect(url_for('queries.index'))

    patterns = Pattern.query.order_by(Pattern.id).all()
    # FIXME this conversion should go when the new database is in
    patterndict = [{
        "id": abs(p.id),
        "template": p.template,
        "explanation": p.explanation,
        "retired": p.id < 0
    } for p in patterns]

    return render_template('queries/create.html',
                           patterns=patterndict)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    query = Query.query.filter_by(id=id).first()
    if request.method == 'POST':

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
            ),
            path=query.path
        )

        query.delete()
        query.write()
        return jsonify(success=True)

    patterns = Pattern.query.order_by(Pattern.id).all()
    # FIXME this conversion should go when the new database is in
    patterndict = [{
        "id": abs(p.id),
        "template": p.template,
        "explanation": p.explanation,
        "retired": p.id < 0
    } for p in patterns]

    return render_template('queries/update.html',
                           query=query,
                           patterns=patterndict)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    query = Query.query.filter_by(id=id).first()
    os.rename(query.path, query.path + ".bak")
    query.delete()
    return redirect(url_for('queries.index'))


def patch_query_results(result):
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


def add_gold(result, cwb_id, pattern):

    try:
        gold = read_csv(
            os.path.join("library", cwb_id, "gold", "adjudicated.tsv"),
            sep="\t", index_col=0
        )
    except FileNotFoundError:
        result['TP'] = None
    else:
        # pre-process gold
        gold = gold.loc[gold['pattern'] == pattern]
        gold = gold.loc[gold['tweet'].isin(list(result['tweet_id']))].rename(
            {'tweet': 'tweet_id'}, axis=1
        )
        tps = gold.rename({'annotation': 'TP'}, axis=1).set_index('tweet_id')
        # join explicit TPs and FPs
        result = result.set_index('tweet_id')
        result = result.join(tps[['TP']], how='left')
        result = result.reset_index()

    return result


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run_cmd(id):
    """
    run a query
    ---
    parameters:
      - name: id
        in: path
        type: int
        required: true
        description: CWB-id of the corpus
      - name: beta
        in: query
        type: bool
        required: false
        default: false
        description: (deprecated) whether to switch to Yuliya's visualization
    """

    # get corpus from settings
    cwb_id = session['corpus']['resources']['cwb_id']

    # run the old query
    query = Query.query.filter_by(id=id).first().serialize()
    oldresult = query_corpus(query, cwb_id)

    if oldresult is None:
        return 'query does not have any matches'

    # pass to frontend
    display_columns = [x for x in oldresult.columns if x not in [
        'context_id', 'context', 'contextend'
    ]]

    patterns = Pattern.query.order_by(Pattern.id).all()
    # FIXME this conversion should go when the new database is in
    patterndict = [{
        "id": abs(p.id),
        "template": p.template,
        "explanation": p.explanation,
        "retired": p.id < 0
    } for p in patterns]

    if request.method == 'POST':

        # create new query
        newquery = dict(
            cqp=request.form['query'],
            meta=dict(
                name=request.form['name'],
                pattern_id=request.form['pattern'],
            ),
            anchors=dict(
                corrections=json.loads(request.form['corrections'].replace(
                    "None", "null"
                )),
                slots=json.loads(request.form['slots'].replace(
                    "None", "null"
                ))
            )
        )

        # get new result and merge to old result
        newresult = query_corpus(newquery, cwb_id)
        result = newresult.merge(
            oldresult, how='outer', on=['tweet_id', 'match..matchend_word'],
            indicator=True
        )
        result = result.drop(
            [x for x in result.columns if x.startswith('match..matchend_')], axis=1
        )
        result = add_gold(result, cwb_id, pattern=query['meta']['pattern'])

        # get TPs, FPs, precision
        tps = result['TP'].value_counts().to_dict()
        tps['TP'] = tps.pop(True, 0)
        tps['FP'] = tps.pop(False, 0)
        try:
            tps['prec'] = tps['TP'] / (tps['FP'] + tps['TP'])
        except ZeroDivisionError:
            tps['prec'] = 'nan'

        # render result
        result = patch_query_results(result)
        return render_template('queries/result_table.html',
                               result=result,
                               patterns=patterndict,
                               tps=tps)

    return Response(
        oldresult[display_columns].to_csv(),
        mimetype='text/csv',
        headers={"Content-disposition":
                 f"attachment; filename={id}-results.csv"}
    )


@click.command('query')
@click.argument('pattern', required=False)
@click.argument('dir_out', required=False)
@click.argument('cwb_id', default="BREXIT_V20190522_DEDUP")
@with_appcontext
def query_command(pattern, dir_out, cwb_id):

    # output directory
    if dir_out is None:
        dir_out = os.path.join(
            current_app.instance_path, cwb_id, "results"
        )
    os.makedirs(dir_out, exist_ok=True)

    # get all queries belonging to the pattern
    if pattern is None:
        queries = Query.query.all()
        current_app.logger.info(
            "all patterns: %d queries" % len(queries)
        )
        path_summary = os.path.join(dir_out, "summary.tsv")
    else:
        queries = Query.query.filter_by(pattern_id=pattern).all()
        current_app.logger.info(
            "pattern %s: %d queries" % (str(pattern), len(queries))
        )
        path_summary = os.path.join(dir_out, str(pattern) + "-summary.tsv")

    # loop through queries
    summary = defaultdict(list)
    for query in queries:

        current_app.logger.info(query.name)

        p_out = None
        n_hits = None
        n_unique = None

        error = ""
        try:
            query = Query.query.filter_by(id=query.id).first()
            lines = query_corpus(query.serialize(), cwb_id)
        except KeyboardInterrupt:
            return

        if lines is not None:
            p_out = os.path.join(dir_out, query.name + '.tsv')
            lines.to_csv(p_out, sep="\t")
            n_hits = len(lines)
            n_unique = len(lines.tweet_id.value_counts())
        else:
            n_hits = 0
            n_unique = 0

        query_pattern = "None" if query.pattern is None else query.pattern.id

        summary['query'].append(query.name)
        summary['pattern'].append(query_pattern)
        summary['n_hits'].append(n_hits)
        summary['n_unique'].append(n_unique)
        summary['path'].append(p_out)
        summary['error'].append(error)

    summary = DataFrame(summary).set_index('query')
    summary.to_csv(path_summary, sep="\t")
