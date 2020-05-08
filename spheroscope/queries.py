import gzip
import sys
import json
import os
import subprocess
from glob import glob

# flask
from flask import (
    Blueprint, g, redirect, render_template, request, url_for, current_app
)
from flask.cli import with_appcontext
from werkzeug.exceptions import abort
import click

# this app
from .auth import login_required
from .db import get_db
from .format_utils import format_query_result
from .corpora import init_corpus


bp = Blueprint('queries', __name__, url_prefix='/queries')


def get_query_from_db(id, check_author=True):

    query = get_db().execute(
        'SELECT qu.id, name, query, modified, author_id,'
        ' username, anchors, regions, pattern'
        ' FROM queries qu JOIN users u ON qu.author_id = u.id'
        ' WHERE qu.id = ?',
        (id,)
    ).fetchone()

    if query is None:
        abort(404, "query id {0} doesn't exist.".format(id))

    if check_author and query['author_id'] != g.user['id']:
        abort(403)

    # format result
    query = dict(query)
    query['anchors'] = json.loads(query['anchors'])
    query['regions'] = json.loads(query['regions'])

    return query


def get_queries_from_db(pattern=None):

    if pattern is None:
        sql_select = (
            'SELECT id FROM queries ORDER BY name ASC'
        )
    else:
        sql_select = (
            'SELECT id FROM queries ORDER BY name ASC WHERE pattern = ?',
            (pattern,)
        )

    rows = get_db().execute(sql_select).fetchall()
    queries = list()

    for row in rows:
        queries.append(get_query_from_db(row['id']))

    return queries


def get_query_from_path(path):

    try:
        with open(path, "rt") as f:
            query = json.loads(f.read())
    except json.JSONDecodeError:
        current_app.logger.error("not a valid query file: %s" % path)
        query = None

    return query


def write_query(query, write_db=True, write_file=True):

    if write_db:
        current_app.logger.info("writing query %s to database" % query['name'])
        insert = (
            "INSERT INTO queries "
            "(author_id, name, query, anchors, regions, pattern) "
            "VALUES (?, ?, ?, ?, ?, ?);"
        )
        db = get_db()
        db.execute(insert, (1,
                            query['name'],
                            query['query'],
                            json.dumps(query['anchors']),
                            json.dumps(query['regions']),
                            query['pattern']))
        db.commit()

    if write_file:
        lib_path = current_app.config['LIB_PATH']
        path = os.path.join(lib_path, "queries", query['name'] + ".query")
        current_app.logger.info("writing query %s to %s" % (query['name'], path))
        with open(path, "wt") as f:
            f.write(json.dumps(query, indent=4))


def delete_from_db(id):
    get_query_from_db(id)
    db = get_db()
    db.execute('DELETE FROM queries WHERE id = ?', (id,))
    db.commit()


def queries_lib2db(lib_path):

    paths = glob(os.path.join(lib_path, 'queries', '*'))
    queries = list()
    for p in paths:
        query = get_query_from_path(p)
        if query is not None:
            write_query(query, write_file=False)
            queries.append(query)
    return queries


@bp.route('/')
@login_required
def index():
    queries = get_queries_from_db()
    return render_template('queries/index.html', queries=queries)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        query = {
            'name': request.form['name'],
            'query': request.form['query'],
            'pattern': request.form['pattern'],
            'anchors': json.loads(request.form['anchors'].replace(
                "None", "null").replace("\'", "\"")),
            'regions': json.loads(request.form['regions'].replace(
                "None", "null").replace("\'", "\""))
        }

        if not query['name']:
            current_app.logger.error('name is required.')

        else:
            write_query(query)
            return redirect(url_for('queries.index'))

    return render_template('queries/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    query = get_query_from_db(id)
    if request.method == 'POST':
        query = {
            'name': request.form['name'],
            'query': request.form['query'],
            'pattern': request.form['pattern'],
            'anchors': json.loads(request.form['anchors'].replace(
                "None", "null").replace("\'", "\"")),
            'regions': json.loads(request.form['regions'].replace(
                "None", "null").replace("\'", "\""))
        }

        if not query['name']:
            current_app.logger.error('name is required.')

        else:
            delete_from_db(id)
            write_query(query)
            return redirect(url_for('queries.index'))

    return render_template('queries/update.html', query=query)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    db.execute('DELETE FROM queries WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('queries.index'))


@bp.route('/<int:id>/show_result', methods=('GET', 'POST'))
@login_required
def show_result(id):

    # get query and path to result
    query = get_query_from_db(id)
    dir_result = current_app.config['RESULTS_PATH']
    path_result = os.path.join(dir_result, query['name'] + ".query.json.gz")
    if not os.path.exists(path_result):
        abort(404, "result file %s does not exist" % path_result)

    # load results
    current_app.logger.info("taking result from %s" % path_result)
    with gzip.open(path_result, "rt") as f:
        result = json.loads(f.read())

    # format result
    result = format_query_result(result)

    # run fillform
    if "FILLFORM" in current_app.config.keys():
        path_patterns = "instance-stable/patterns.csv"
        fillform_result = subprocess.run("{} table {} {}".format(
            current_app.config['FILLFORM'], path_patterns, path_result
        ), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        errors = fillform_result.stderr.decode("utf-8")
        if len(errors) > 0:
            current_app.logger.warning(
                "%s says: %s" % (current_app.config['FILLFORM'], errors)
            )
        table = fillform_result.stdout.decode("utf-8")
    else:
        table = None

    # render result
    return render_template('queries/show_result.html',
                           result=result,
                           table=table)


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run(id, show=True):

    # get
    query = get_query_from_db(id)

    # path for results
    dir_result = current_app.config['RESULTS_PATH']
    if not os.path.isdir(dir_result):
        os.makedirs(dir_result)
    path_result = os.path.join(dir_result, query['name'] + ".query.json.gz")

    # create result
    corpus = init_corpus(current_app.config)
    current_app.logger.info("querying corpus")
    try:
        result, info = corpus.query(query['query'],
                                    s_break=current_app.config['S_BREAK'],
                                    context=None,
                                    match_strategy='longest',
                                    info=True)
    except TypeError:
        abort(
            404,
            "query id %d does not have any results in corpus %s\n%s" % (
                id,
                current_app.config['CORPUS_NAME'],
                query['query']
            )
            )
    query['info'] = info
    concordance = corpus.concordance(result)
    query['result'] = concordance.show_argmin(
        query['anchors'],
        query['regions'],
        p_show=['lemma']
    )
    query['modified'] = str(query['modified'])

    # dump result
    current_app.logger.info("dumping result to %s" % path_result)
    with gzip.open(path_result, 'wt') as f_out:
        json.dump(query, f_out, indent=4)

    if show:
        return redirect(url_for('queries.show_result', id=id))


def run_all_queries():

    from ccc.concordances import process_argmin_file
    corpus = init_corpus(current_app.config)

    paths_queries = sorted(glob(
        os.path.join(current_app.config['LIB_PATH'], "queries", "*.query")
    ))
    current_app.logger.info("running all queries")
    for p in paths_queries:
        current_app.logger.info("path: " + p)
        dir_result = current_app.config['RESULTS_PATH']
        if not os.path.isdir(dir_result):
            os.makedirs(dir_result)
        query_name = p.split("/")[-1].split(".")[0]
        path_result = os.path.join(dir_result, query_name + ".query.json.gz")
        try:
            result = process_argmin_file(
                corpus, p, p_show=['lemma'], context=None,
                s_break=current_app.config['S_BREAK'], match_strategy='longest'
            )
        except:
            result = {'error': str(sys.exc_info()[0])}
        with gzip.open(path_result, 'wt') as f_out:
            json.dump(result, f_out, indent=4)


@click.command('run-all-queries')
@with_appcontext
def run_all_queries_command():
    run_all_queries()


def add_run_queries(app):
    app.cli.add_command(run_all_queries_command)
