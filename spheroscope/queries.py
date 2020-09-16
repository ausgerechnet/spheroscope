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
