from flask import (
    Blueprint, g, redirect, render_template, request, url_for, current_app
)
from flask.cli import with_appcontext
from werkzeug.exceptions import abort
import click

from glob import glob
import gzip
import json
import os
import subprocess
import logging

from .auth import login_required
from .db import get_db
from .format_utils import format_query_result


logger = logging.getLogger(__name__)
bp = Blueprint('queries', __name__, url_prefix='/queries')


def get_query_from_db(id, check_author=True):
    query = get_db().execute(
        'SELECT qu.id, name, query, created, author_id,'
        ' username, anchors, regions, pattern'
        ' FROM queries qu JOIN users u ON qu.author_id = u.id'
        ' WHERE qu.id = ?',
        (id,)
    ).fetchone()

    if query is None:
        abort(404, "query id {0} doesn't exist.".format(id))

    if check_author and query['author_id'] != g.user['id']:
        abort(403)

    query = dict(query)
    query.pop('created')
    query['anchors'] = json.loads(query['anchors'])
    query['regions'] = json.loads(query['regions'])

    return query


def get_queries_from_db(pattern=None):

    if pattern is None:
        sql_select = (
            'SELECT qu.id, name, query, created, author_id,'
            ' username, anchors, regions, pattern'
            ' FROM queries qu JOIN users u ON qu.author_id = u.id'
            ' ORDER BY name ASC'
        )
    else:
        sql_select = (
            'SELECT qu.id, name, query, created, author_id,'
            ' username, anchors, regions, pattern'
            ' FROM queries qu JOIN users u ON qu.author_id = u.id'
            ' ORDER BY name ASC WHERE qu.pattern = ?',
            (pattern,)
        )

    db = get_db()
    queries = db.execute(sql_select).fetchall()
    queries = [dict(q) for q in queries]
    return queries


def get_query_from_path(path):

    try:
        with open(path, "rt") as f:
            query = json.loads(f.read())
    except json.JSONDecodeError:
        logger.error("not a valid query file: %s" % path)
        query = None

    return query


def write_query(query, write_db=True, write_file=True):

    if write_db:
        logger.info("writing query %s to database" % query['name'])
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
        dir_out = os.path.join("instance", "queries")
        if not os.path.isdir(dir_out):
            os.makedirs(dir_out)
        path = os.path.join(dir_out, query['name'] + ".txt")
        logger.info("writing query %s to %s" % (query['name'], path))
        with open(path, "wt") as f:
            f.write(json.dumps(query, indent=4))


def delete_from_db(id):
    get_query_from_db(id)
    db = get_db()
    db.execute('DELETE FROM queries WHERE id = ?', (id,))
    db.commit()


def queries_paths2db(paths):

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
            logger.error('name is required.')

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
            logger.error('name is required.')

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

    # get query
    query = get_query_from_db(id)
    # select result file (current / stable)
    path_result = "instance/results/" + query['name'] + ".query.json.gz"
    if not os.path.exists(path_result):
        path_result = "instance-stable/results/" + query['name'] + ".query.json.gz"

    # load results
    with gzip.open(path_result, "rt") as f:
        result = json.loads(f.read())

    # format result
    result = format_query_result(result)

    if "FILLFORM" in current_app.config.keys():
        path_patterns = "instance-stable/patterns.csv"
        fillform_result = subprocess.run("{} table {} {}".format(
            current_app.config['FILLFORM'], path_patterns, path_result
        ), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        errors = fillform_result.stderr.decode("utf-8")
        if len(errors) > 0:
            logger.warning("%s says: %s" % (current_app.config['FILLFORM'], errors))
        return render_template('queries/show_result.html',
                               result=result,
                               table=fillform_result.stdout.decode("utf-8"))

    else:
        return render_template('queries/show_result.html',
                               result=result,
                               table=None,
                               errors=None)


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run(id):

    # get query and path of result
    query = get_query_from_db(id)
    try:
        os.makedirs("instance/results/")
    except OSError:
        pass
    path_result = "instance/results/" + query['name'] + ".query.json.gz"

    corpus = current_app.config['ENGINE']

    # create result
    result, info = corpus.query(query['query'],
                                s_break='s',
                                context=None,
                                match_strategy='longest',
                                info=True)
    query['info'] = info
    concordance = corpus.concordance(result)
    query['result'] = concordance.show_argmin(
        query['anchors'],
        query['regions'],
        p_show=['lemma']
    )

    # dump result
    with gzip.open(path_result, 'wt') as f_out:
        json.dump(query, f_out, indent=4)

    # format result
    result = format_query_result(query)

    # render result
    return render_template('queries/show_result.html',
                           result=result)


def run_all_queries():

    from ccc.concordances import process_argmin_file
    corpus = current_app.config['ENGINE']

    paths_queries = glob(
        os.path.join([current_app.config['LIB_PATH'], "queries", "*.query"])
    )
    logger.info("running all queries")
    for p in paths_queries:
        logger.info("path:" + p)
        p_out = p.replace("queries", "results") + ".json.gz"
        result = process_argmin_file(
            corpus, p, p_show=['lemma'], context=None,
            s_break='s', match_strategy='longest'
        )
        with gzip.open(p_out, 'wt') as f_out:
            json.dump(result, f_out, indent=4)


def add_run_queries(app):
    app.cli.add_command(run_all_queries_command)


@click.command('run-all-queries')
@with_appcontext
def run_all_queries_command():
    run_all_queries()
