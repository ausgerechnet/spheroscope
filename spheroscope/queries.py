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
import codecs
import pandas as pd

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


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run_cmd(id):

    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)

    if result is None:
        return 'query does not have any matches'

    display_columns = [x for x in result.columns if x not in [
        'match', 'matchend', 'context_id', 'context', 'contextend', 'df'
    ]]

    return result[display_columns].to_html(escape=False)

    # if show:
    #     return redirect(url_for('queries.show_result', id=id))


@bp.route('/<int:id>/run2', methods=('GET', 'POST'))
@login_required
def run2_cmd(id):

    # get result
    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)
    # print(result['df'].iloc[1])

    result.to_json(r'table.json')
    # this one is for testing
    result.to_json(r'tableresult.json')

    tojson = result.to_json()
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

        new_tbl = open('table.json', 'w')
        json.dump(tbl, new_tbl)
        new_tbl.close()

    df = pd.read_json('table.json')

    display_columns = [x for x in df.columns if x not in [
        'match', 'matchend', 'context_id', 'context', 'contextend', 'df'
    ]]
    df[display_columns].to_html(
        'showTable.html', escape=False, table_id="query-results"
    )

    file = codecs.open('./showTable.html', 'r', 'utf-8')
    test = file.read()
    return test


@bp.route('/<int:id>/meta', methods=('GET', 'POST'))
@login_required
def show_meta(loc):

    # match und matchend als index für jede zeile

    df = pd.read_html('./showTable.html')[0]

    df['df'].iloc[loc].to_html('./meta.html', escape=False, table_id="meta-df")

    return render_template('newqueries/meta.html')


# @bp.route('/<cwb_id>/<int:id>/show_result', methods=('GET', 'POST'))
# @login_required
# def show_result(cwb_id, id):

#     # load results
#     current_app.logger.info("taking result from %s" % path_result)
#     with gzip.open(path_result, "rt") as f:
#         result = json.loads(f.read())

#     # run fillform
#     if "FILLFORM" in current_app.config.keys():
#         path_patterns = "instance-stable/patterns.csv"
#         fillform_result = subprocess.run("{} table {} {}".format(
#             current_app.config['FILLFORM'], path_patterns, path_result
#         ), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         errors = fillform_result.stderr.decode("utf-8")
#         if len(errors) > 0:
#             current_app.logger.warning(
#                 "%s says: %s" % (current_app.config['FILLFORM'], errors)
#             )
#         table = fillform_result.stdout.decode("utf-8")
#     else:
#         table = None

#     # render result
#     return render_template('queries/show_result.html',
#                            result=result,
#                            table=table)

# def run_all_queries():

#     from ccc.concordances import process_argmin_file
#     corpus = init_corpus(current_app.config)

#     paths_queries = sorted(glob(
#         os.path.join(current_app.config['LIB_PATH'], "queries", "*.query")
#     ))
#     current_app.logger.info("running all queries")
#     for p in paths_queries:
#         current_app.logger.info("path: " + p)
#         dir_result = current_app.config['RESULTS_PATH']
#         if not os.path.isdir(dir_result):
#             os.makedirs(dir_result)
#         query_name = p.split("/")[-1].split(".")[0]
#         path_result = os.path.join(dir_result, query_name + ".query.json.gz")
#         try:
#             result = process_argmin_file(
#                 corpus, p, p_show=['lemma'], context=None,
#                 s_break=current_app.config['S_BREAK'], match_strategy='longest'
#             )
#         except:
#             current_app.logger.error('unexpected error in path "%s"' % p)
#             result = {'error': str(sys.exc_info()[0])}
#         with gzip.open(path_result, 'wt') as f_out:
#             json.dump(result, f_out, indent=4)


# @click.command('run-all-queries')
# @with_appcontext
# def run_all_queries_command():
#     run_all_queries()


# def add_run_queries(app):
#     app.cli.add_command(run_all_queries_command)
