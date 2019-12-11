from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from spheroscope.auth import login_required
from spheroscope.db import get_db
import gzip
import json


bp = Blueprint('queries', __name__, url_prefix='/queries')


@bp.route('/')
@login_required
def index():
    db = get_db()
    queries = db.execute(
        'SELECT qu.id, title, query, created, author_id, username, anchors, regions, pattern'
        ' FROM queries qu JOIN users u ON qu.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('queries/index.html', queries=queries)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        query = request.form['query']
        error = None

        if not title:
            error = 'title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO queries (title, query, author_id)'
                ' VALUES (?, ?, ?)',
                (title, query, g.user['id'])
            )
            db.commit()
            return redirect(url_for('queries.index'))

    return render_template('queries/create.html')


def get_query(id, check_author=True):
    query = get_db().execute(
        'SELECT qu.id, title, query, created, author_id, username, anchors, regions, pattern'
        ' FROM queries qu JOIN users u ON qu.author_id = u.id'
        ' WHERE qu.id = ?',
        (id,)
    ).fetchone()

    if query is None:
        abort(404, "query id {0} doesn't exist.".format(id))

    if check_author and query['author_id'] != g.user['id']:
        abort(403)

    query = dict(query)
    query['anchors'] = json.loads(query['anchors'])
    query['regions'] = json.loads(query['regions'])

    return query


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_query(id)
    db = get_db()
    db.execute('DELETE FROM queries WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('queries.index'))


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    query = get_query(id)
    if request.method == 'POST':
        title = request.form['title']
        query = request.form['query']
        error = None

        if not title:
            error = 'title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE queries SET title = ?, query = ?'
                ' WHERE id = ?',
                (title, query, id)
            )
            db.commit()
            return redirect(url_for('queries.index'))

    return render_template('queries/update.html', query=query)


@bp.route('/<int:id>/show_result', methods=('GET', 'POST'))
@login_required
def show_result(id):

    query = get_query(id)
    path_result = "instance/results/" + query['title'] + ".query.json.gz"
    with gzip.open(path_result, "rt") as f:
        result = json.loads(f.read())
    print(result.keys())
    return render_template('queries/show_result.html', query=query, result=result)


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run(id):
    from ccc.anchors import anchor_query
    from ccc.cwb import CWBEngine
    ENGINE = CWBEngine(
        {'name': 'BREXIT_V20190522',
         'lib_path': "/home/ausgerechnet/projects/spheroscope/app/instance/lib/"},
        "/home/ausgerechnet/corpora/cwb/registry"
    )
    query = get_query(id)
    conc = anchor_query(ENGINE,
                        query['query'], query['anchors'], query['regions'],
                        'tweet')
    return render_template('queries/run.html', query=query, concordances=conc)
