from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from spheroscope.auth import login_required
from spheroscope.db import get_db

import pandas as pd
import gzip
import json
import subprocess
import os
from collections import Counter


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
    query.pop('created')
    query['name'] = query.pop('title')
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


def format_query_result(query):

    # init result
    result = dict()
    result['query'] = query['query']
    result['pattern'] = query['pattern']
    result['name'] = query['name']

    # get matches
    if 'matches' in query['result'].keys():
        result['matches'] = query['result']['matches']
    else:
        result['matches'] = None

    # format anchors
    anchors = pd.DataFrame(query['anchors'])
    anchors.columns = ['number', 'correction', 'hole', 'clear name']
    result['anchors'] = anchors.to_html(escape=False, index=False)

    # format regions
    regions = pd.DataFrame(query['regions'])
    regions.columns = ['start', 'end', 'hole', 'clear name']
    result['regions'] = regions.to_html(escape=False, index=False)

    # format anchor words
    counts = dict()
    for key in query['result']['anchor_words'].keys():
        df = pd.DataFrame.from_dict(
            Counter(query['result']['anchor_words'][key]), orient='index'
        ).sort_values(by=0, ascending=False)
        df.columns = ['freq']
        df.index.name = key
        counts[key] = df.to_html(escape=False, index_names=True, bold_rows=False)
    result['anchor_words'] = counts

    # format regions_words
    counts = dict()
    for key in query['result']['regions_words'].keys():
        words = [" ".join(r) for r in query['result']['regions_words'][key]]
        df = pd.DataFrame.from_dict(
            Counter(words), orient='index'
        ).sort_values(by=0, ascending=False)
        df.columns = ['freq']
        df.index.name = key
        counts[key] = df.to_html(escape=False,
                                 index_names=True,
                                 bold_rows=False)
    result['region_words'] = counts

    # return
    return result


@bp.route('/<int:id>/show_result', methods=('GET', 'POST'))
@login_required
def show_result(id):

    # get query
    query = get_query(id)
    # select result file (current / stable)
    path_result = "instance/results/" + query['name'] + ".query.json.gz"
    if not os.path.exists(path_result):
        path_result = "instance-stable/results/" + query['name'] + ".query.json.gz"

    # load results
    with gzip.open(path_result, "rt") as f:
        query = json.loads(f.read())

    # format result
    result = format_query_result(query)

    # render result
    return render_template('queries/show_result.html',
                           result=result)

    # # run fill-form
    # path_patterns = "instance-stable/patterns.csv"
    # fillform_result = subprocess.run("fillform-static table {} {}".format(
    #     path_patterns, path_result
    # ), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # return render_template('queries/show_result.html',
    #                        result=result,
    #                        table=fillform_result.stdout.decode("utf-8"),
    #                        errors=fillform_result.stderr.decode("utf-8"))


@bp.route('/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run(id):

    # get query and path of result
    query = get_query(id)
    try:
        os.makedirs("instance/results/")
    except OSError:
        pass
    path_result = "instance/results/" + query['name'] + ".query.json.gz"

    # create result
    from ccc.cwb import CWBEngine
    from ccc.anchors import anchor_query
    corpus_settings = {
            'name': current_app.config['CORPUS_NAME'],
            'lib_path': current_app.config['LIB_PATH']
        }
    engine = CWBEngine(
        corpus_settings,
        current_app.config['REGISTRY_PATH']
    )
    subcorpus = (
        "DEDUP=/region[tweet,a] :: (a.tweet_duplicate_status!='1') within tweet;"
        "DEDUP;"
    )
    engine.cqp.Exec(subcorpus)
    concordance_settings = {
        'order': 'first',
        'cut_off': None,
        'p_query': 'lemma',
        's_break': 'tweet',
        'match_strategy': 'longest'
    }
    query['result'] = anchor_query(engine,
                                   query['query'], query['anchors'], query['regions'],
                                   concordance_settings['s_break'], concordance_settings['match_strategy'])
    query['concordance_settings'] = concordance_settings

    # dump result
    with gzip.open(path_result, 'wt') as f_out:
        json.dump(query, f_out, indent=4)

    # format result
    result = format_query_result(query)

    # render result
    return render_template('queries/show_result.html',
                           result=result)

    # # run fill-form
    # path_patterns = "instance-stable/patterns.csv"
    # fillform_result = subprocess.run("fillform-static table {} {}".format(
    #     path_patterns, path_result
    # ), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # return render_template('queries/show_result.html',
    #                        result=result,
    #                        table=fillform_result.stdout.decode("utf-8"),
    #                        errors=fillform_result.stderr.decode("utf-8"))
