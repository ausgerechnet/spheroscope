#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
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


@bp.route('/index2')
@login_required
def index2():
    queries = Query.query.order_by(Query.name).all()
    return render_template('queries/index2.html',
                           queries=queries)


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


def add_gold(result, pattern=None):

    # get gold
    gold = read_csv(
        os.path.join("library", "gold.tsv"), sep="\t", index_col=0
    )
    if pattern is not None:
        gold = gold.loc[gold['pattern'] == pattern]
    gold = gold.loc[gold['tweet'].isin(list(result['tweet_id']))].rename(
        {'tweet': 'tweet_id'}, axis=1
    )

    # join explicit TPs and FPs
    pos = gold.loc[gold['annotation']].rename(
        {'annotation': 'TP'}, axis=1
    ).set_index('tweet_id')
    neg = gold.loc[~gold['annotation']].rename(
        {'annotation': 'FP'}, axis=1
    ).set_index('tweet_id')
    result = result.set_index('tweet_id')
    result = result.join(pos[['TP']], how='left')
    result = result.join(neg[['FP']], how='left')
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

    # switch to Yuliya's implementation?
    beta = request.args.get('beta', False)

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

    if not beta:
        if request.method == 'POST':
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
            newresult = query_corpus(newquery, cwb_id)
            result = newresult.merge(
                oldresult, how='outer', on='tweet_id', indicator=True
            )
            result = add_gold(result, pattern=query['meta']['pattern'])
            result = patch_query_results(result)
            return render_template('queries/result_table.html',
                                   result=result,
                                   patterns=patterndict)

        return Response(
            oldresult[display_columns].to_csv(),
            mimetype='text/csv',
            headers={"Content-disposition":
                     f"attachment; filename={id}-results.csv"}
        )

    else:

        tojson = oldresult.to_json()
        tbl = json.loads(tojson)

        for idx in tbl["text"]:

            regions = []

            for col in tbl:
                if re.findall(r'\d\_\w+', col):
                    regions.append(col)

            # txt = (tbl["text"][idx]).lower()  # <- pure Tweet
            cpos_dict = tbl["df"][idx]["word"]
            match_dict = tbl["df"][idx]["match"]
            matchend_dict = tbl["df"][idx]["matchend"]

            # temporary list
            tmp_2 = []
            # all of the possible anchors for this query
            anchor_points = []

            for i in tbl["df"][idx]:
                if re.findall(r'\b\d+\b', i):
                    anchor_points.append(["a" + str(i)])

            tupl = []

            for k in cpos_dict:

                word = cpos_dict[k]
                w_pos = k

                is_matchbeg = match_dict[k]
                is_matchend = matchend_dict[k]

                anchor_points_in = [
                    ai[0] for ai in anchor_points if tbl["df"][idx][str(ai[0])[-1]][w_pos]
                ]

                tupl = [word, w_pos, is_matchbeg, is_matchend, anchor_points_in]

                if is_matchbeg:
                    tupl.insert(0, '<span class="match-highlight">')
                elif is_matchend:
                    tupl.insert(5, '</span>')

                for i in anchor_points_in:

                    if int(i[-1]) % 2 == 0:
                        tupl.insert(tupl.index(word), '<sub class="anchor">{s}</sub>'.format(s=i[-1]))
                        if len(regions) > 0:
                            tupl.insert(tupl.index(word), '<span class="anchor-highlight">')
                    elif int(i[-1]) % 2 != 0:
                        if len(regions) > 0:
                            tupl.insert(tupl.index(word) + 1, '</span>')
                        tupl.insert(tupl.index(word) + 1, '<sub class="anchor">{s}</sub>'.format(s=i[-1]))

                tupl.remove(w_pos)
                tupl.remove(is_matchbeg)
                tupl.remove(is_matchend)
                tupl.remove(anchor_points_in)

                for i in tupl:
                    tmp_2.append(i)

            res = ' '.join(tmp_2)

            tbl["text"][idx] = res

        df = DataFrame.from_dict(tbl)
        display_columns = ['tweet_id', 'text']
        return df[display_columns].to_html(escape=False, table_id="query-results")


@click.command('query')
@click.argument('dir_out')
@click.argument('pattern', default=None, required=False)
@click.argument('cwb_id', default="BREXIT_V20190522_DEDUP")
@with_appcontext
def query_command(pattern, dir_out, cwb_id):

    os.makedirs(dir_out, exist_ok=True)

    # get all queries belonging to the pattern
    if pattern is None:
        queries = Query.query.all()
        current_app.logger.info(
            "%d queries" % len(queries)
        )
        path_summary = os.path.join(dir_out, "summary.tsv")
    else:
        queries = Query.query.filter_by(pattern_id=pattern).all()
        current_app.logger.info(
            "pattern %s: %d queries" % (str(pattern), len(queries))
        )
        path_summary = os.path.join(dir_out, str(pattern) + "-summary.tsv")

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

    summary = DataFrame(summary)
    summary.to_csv(path_summary, sep="\t")
