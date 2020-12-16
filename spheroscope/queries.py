#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from ccc.queries import run_query

from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g, session
)

from .auth import login_required
from .corpora import read_config, init_corpus
from .database import Query

import re
import json
from pandas import DataFrame

bp = Blueprint('queries', __name__, url_prefix='/queries')


def run(id, cwb_id):

    # get query
    query = Query.query.filter_by(id=id).first().serialize()

    # get corpus config
    corpus_config = read_config(cwb_id)

    # make sure anchors are int
    corrections_int = dict()
    for k in query['anchors']['corrections'].keys():
        c = query['anchors']['corrections'][k]
        corrections_int[int(k)] = c
    query['anchors']['corrections'] = corrections_int

    # load query and display parameters
    query['query'] = dict(corpus_config['query'])
    query['query']['context'] = None
    query['display'] = dict(corpus_config['display'])

    # run query
    current_app.logger.info('running query')
    corpus = init_corpus(corpus_config)
    lines = run_query(corpus, query)

    # result_parameters = [query[key] for key in query.keys() if key not in [
    #     'id', 'user_id', 'modified', 'pattern'
    # ]]
    # param = generate_idx(result_parameters, prefix='param-', length=10)

    # # determine path to result
    # dir_result = os.path.join(current_app.instance_path, cwb_id, 'matches', param)
    # if not os.path.isdir(dir_result):
    #     os.makedirs(dir_result)
    # path_result = os.path.join(dir_result, query['name'] + ".tsv.gz")

    # # save result
    # current_app.logger.info('saving result')
    # conc.to_csv(path_result, sep="\t")

    return lines


######################################################
# ROUTING ############################################
######################################################

@bp.route('/')
@login_required
def index():
    queries = Query.query.order_by(Query.name).all()
    return render_template('queries/index.html',
                           queries=queries)


@bp.route('/<int:id>/<name>/matches', methods=('GET', 'POST'))
@login_required
def matches(id, name):

    beta = request.args.get('beta', False)
    query_id = id
    query_name = name
    query_table = run_cmd(query_id, beta)
    frequency_table = frequency_table_list(query_id)
    meta_data = meta_data_list(query_id)
    selected_query = select_query(query_id)
    return render_template('queries/matches.html', query_table=query_table, meta_data=meta_data, query_name=query_name,
                           frequency_table=frequency_table, selected_query=selected_query)


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
                current_app.instance_path, cwb_id, 'wordlists',
                request.form['name'] + ".txt"
            ),
            user_id=g.user.id
        )
        query.write()

        return redirect(url_for('queries.index'))

    return render_template('queries/create.html')


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
        return redirect(url_for('queries.index'))

    return render_template('queries/update.html',
                           query=query)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    query = Query.query.filter_by(id=id).first()
    query.delete()
    return redirect(url_for('queries.index'))


#@bp.route('/<int:id>/query', methods=('GET', 'POST'))
#@login_required
def select_query(id):

    shown_query = Query.query.filter_by(id=id).first()
    return render_template('queries/query.html',
                           shown_query=shown_query)


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
def run_cmd(id, beta):

    #beta = request.args.get('beta', False)
    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)
    #print(beta)

    if result is None:
        return 'query does not have any matches'

    #print(str(result["0_lemma"].value_counts()))

    display_columns = [x for x in result.columns if x not in [
        'match', 'matchend', 'context_id', 'context', 'contextend', 'df'
    ]]

    if not beta:
        return result[display_columns].to_html(escape=False)

    else:

        tojson = result.to_json()
        tbl = json.loads(tojson)

        for idx in tbl["text"]:

            # Metadaten => result['df'].iloc[tweet_idx]
            # df_to_str = str(result['df'].iloc[tweet_idx])

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
        return df.to_html(escape=False, table_id="query-results", columns=display_columns)


def meta_data_list(id):

    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)

    if result is None:
        return 'query does not have any matches'

    tojson = result.to_json()
    tbl = json.loads(tojson)
    tweet_idx = 0
    meta_dict = {}

    for idx in tbl["text"]:
        df_to_str = result['df'].iloc[tweet_idx].to_html(escape=False)
        meta_dict[idx] = df_to_str
        tweet_idx += 1

    md = json.dumps(meta_dict)

    return md


def frequency_table_list(id):

    # df['x_lemma'].value_counts()
    # x steht für eine Region z.B. vom Ankerpunkt 0 bis 1

    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)

    if result is None:
        return 'query does not have any matches'

    tojson = result.to_json()
    tbl = json.loads(tojson)
    frequency_dict = {}

    #print(result["0_lemma"].value_counts())

    for idx in tbl["text"]:

        # Regions

        regions = []
        freq_tables = ""

        for col in tbl:
            if re.findall(r'\d\_\w+', col):
                regions.append(col)

        for region in regions:
            freq_tables += (str(result[region].value_counts()))

        frequency_dict[idx] = freq_tables

    freq = json.dumps(frequency_dict)
    #print(frequency_dict)

    return freq
