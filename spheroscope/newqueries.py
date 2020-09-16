#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
# import json
# import re
# import pandas as pd
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
@bp.route('/')
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

    # write data to disk in different formats for Yuliya to inspect
    result.to_json('table.json')
    result.to_csv('table.csv')
    result.to_html('table.html')
    # tmp = result.to_json()
    # tbl = json.loads(tmp)

    # move index to columns to be able to work with
    result = result.reset_index()

    # we will use the following list to collect the results
    # NB this is way faster than updating the dataframe each time
    texts = list()

    for text, match, matchend, context, contextend in zip(result["text"], result["match"], result["matchend"], result["context"], result["contextend"]):

        txt = text.lower()      # <- Tweet
        tmp = txt.split()       # <- Aufteilung

        # match beginn
        # matchcontext = [int(s) for s in re.findall(r'\b\d+\b', idx)]
        # # match = (result["match_lemma"][idx])

        # match = [s for s in tmp if s.startswith(result["match_lemma"][idx][:-1])][0]  # <- Anfang vom Match-Bereich

        # insertbeg = [s for s in tmp if s.startswith(match)][0]
        # insertend = tmp[tmp.index(insertbeg) + (matchcontext[1] - matchcontext[0])]  # <- Ende vom Match-Bereich

        # now we can just work with relative positions
        insertbeg = match - context
        insertend = matchend - context + 2

        tmp.insert(insertbeg, '<span class="match-highlight">')
        tmp.insert(insertend, '</span>')
        res = ' '.join(tmp)

        texts.append(res)

        # schreibe 'res' in Pandas df
        # result["text"][idx] = res

        # new_result = open('table.json', 'w')
        # json.dump(result, new_result)
        # new_result.close()

    result['text'] = texts
    # df = pd.read_json('table.json')
    cols = ["tweet_id", "text"]
    result.to_html('showTable.html',
                   escape=False,
                   table_id="query-results",
                   columns=cols)

    # here's where the magic happens
    file = codecs.open('showTable.html', 'r', 'utf-8')
    test = file.read()
    return test
