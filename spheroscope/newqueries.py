#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import codecs

from ccc.queries import run_query

from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g, session
)

from .auth import login_required
from .corpora import read_config, init_corpus
from .database import Query


bp = Blueprint('newqueries', __name__, url_prefix='/newqueries')


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
@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    queries = Query.query.order_by(Query.name).all()
    return render_template('newqueries/index.html',
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
                current_app.instance_path, cwb_id, 'wordlists',
                request.form['name'] + ".txt"
            ),
            user_id=g.user.id
        )
        query.write()

        return redirect(url_for('newqueries.index'))

    return render_template('newqueries/create.html')


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
        return redirect(url_for('newqueries.index'))

    return render_template('newqueries/update.html',
                           query=query)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    query = Query.query.filter_by(id=id).first()
    query.delete()
    return redirect(url_for('newqueries.index'))


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run_cmd(id):

    # get result
    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)

    result.to_json(r'table.json')
    # this one is for testing
    result.to_json(r'tableresult.json')

    tojson = result.to_json()
    tbl = json.loads(tojson)

    # old/full table

    # display_columns = [x for x in result.columns if x not in [
    #     'match', 'matchend', 'context_id', 'context', 'contextend', 'df'
    # ]]
    # r_test_alt = result[display_columns].to_html(escape=False, table_id="query-results")

    # print(display_columns)

    # create html file from table
    # r_test = result[display_columns].to_html("table.html")
    # result[display_columns].to_html("table.html")

    # print(r_test)

    for idx in tbl["text"]:

        txt = (tbl["text"][idx]).lower()  # <- pure Tweet

        # print(txt)

        tmp = txt.split()

        # print(tmp)

        # cpos:

        cpos = list(tbl["df"][idx]["lemma"].keys())

        # beginning and end positions of the match:

        match = list(tbl["df"][idx]["match"].values())
        matchend = list(tbl["df"][idx]["matchend"].values())

        # temporary list

        tmp_2 = []

        for word in tmp:

            w_pos = cpos[tmp.index(word)]

            is_matchbeg = match[tmp.index(word)]
            is_matchend = matchend[tmp.index(word)]

            a0 = tbl["df"][idx]["0"][w_pos]
            a1 = tbl["df"][idx]["1"][w_pos]
            a2 = tbl["df"][idx]["2"][w_pos]
            a3 = tbl["df"][idx]["3"][w_pos]

            # there can be a max. of 10 anchor points

            #anchor_points = []

           # for i in anchor_points:

            #    if tbl["df"][idx][i][w_pos] :

            anchor_points = [["a0", a0], ["a1", a1], ["a2", a2], ["a3", a3]]
            anchor_points = [ai[0] for ai in anchor_points if ai[1] == True]

            tupl = [word, w_pos, is_matchbeg, is_matchend, anchor_points]

            if is_matchbeg:
                tupl.insert(0, '<span class="match-highlight">')
            elif is_matchend:
                tupl.insert(5, '</span>')

            if "a0" in anchor_points:
                tupl.insert(tupl.index(word), '<sub class="anchor">0</sub>')
                tupl.insert(tupl.index(word), '<span class="anchor-highlight">')

            if "a1" in anchor_points:
                tupl.insert(tupl.index(word) + 1, '</span>')
                tupl.insert(tupl.index(word) + 1, '<sub class="anchor">1</sub>')

            if "a2" in anchor_points:
                tupl.insert(tupl.index(word), '<sub class="anchor">2</sub>')
                tupl.insert(tupl.index(word), '<span class="anchor-highlight">')

            if "a3" in anchor_points:
                tupl.insert(tupl.index(word) + 1, '</span>')
                tupl.insert(tupl.index(word) + 1, '<sub class="anchor">3</sub>')

            tupl.remove(w_pos)
            tupl.remove(is_matchbeg)
            tupl.remove(is_matchend)
            tupl.remove(anchor_points)

            for i in tupl:
                # print(i)
                tmp_2.append(i)

        print(tmp_2)

        res = ' '.join(tmp_2)

        # schreibe 'res' in Pandas df

        tbl["text"][idx] = res

        new_tbl = open('table.json', 'w')
        json.dump(tbl, new_tbl)
        new_tbl.close()

    df = pd.read_json('table.json')

    display_columns = [x for x in df.columns if x not in [
        'match', 'matchend', 'context_id', 'context', 'contextend', 'df'
    ]]
    cols = ["text"]
    df[display_columns].to_html('showTable.html', escape=False, table_id="query-results", columns=cols)
    file = codecs.open('./showTable.html', 'r', 'utf-8')
    test = file.read()
    return test
