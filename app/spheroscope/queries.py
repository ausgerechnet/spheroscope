from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from spheroscope.auth import login_required
from spheroscope.db import get_db

import pandas as pd
import gzip
import json
import os
from collections import Counter
import subprocess

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


def format_query_result(query_result):

    # init result
    result = dict()
    result['query'] = query_result['query']
    result['pattern'] = query_result['pattern']

    # TODO make consistent
    if 'name' in query_result.keys():
        result['title'] = query_result['name']
    else:
        result['title'] = query_result['title']

    # format anchors
    anchors = pd.DataFrame(query_result['anchors'])
    anchors.columns = ['number', 'correction', 'hole', 'clear name']
    result['anchors'] = anchors.to_html(escape=False, index=False)

    # format regions
    regions = pd.DataFrame(query_result['regions'])
    if not regions.empty:
        regions.columns = ['start', 'end', 'hole', 'clear name']
        result['regions'] = regions.to_html(escape=False, index=False)
    else:
        result['regions'] = None

    # get matches
    if 'matches' in query_result['result'].keys():
        result['matches'] = list()
        for key in query_result['result']['matches'].keys():

            # get holes
            holes = query_result['result']['matches'][key].pop('holes')

            # get rid of the offset
            query_result['result']['matches'][key].pop('offset')

            # format anchor column
            df = pd.DataFrame(query_result['result']['matches'][key], dtype=str)
            df.fillna(-1, inplace=True)
            df['anchor'] = df['anchor'].apply(pd.to_numeric, downcast='integer')
            df = df.replace(-1, "")

            # format match column
            df['match'] = df['match'].replace("False", "")
            df['match'] = df['match'].replace("True", "match")

            seq = " ".join(
                query_result['result']['matches'][key]['word'].values()
            )
            line = {
                'full': seq,
                'position': key,
                'holes': holes,
                'df': df.to_html(
                    escape=False, index_names='cpos', bold_rows=False
                )
            }
            result['matches'].append(line)
        result['nr_matches'] = query_result['result']['nr_matches']
    else:
        result['matches'] = list()
        result['nr_matches'] = 0

    # frequency count of holes
    counts = dict()
    for key in query_result['result']['holes'].keys():
        df = pd.DataFrame.from_dict(
            Counter(query_result['result']['holes'][key]), orient='index'
        ).sort_values(by=0, ascending=False)
        df.columns = ['freq']
        df.index.name = key
        counts[key] = df.to_html(escape=False, index_names=True, bold_rows=False)
    result['holes'] = counts

    # return
    return result


@bp.route('/<int:id>/show_result', methods=('GET', 'POST'))
@login_required
def show_result(id):

    # get query
    query = get_query(id)
    # select result file (current / stable)
    path_result = "instance/results/" + query['title'] + ".query.json.gz"
    if not os.path.exists(path_result):
        path_result = "instance-stable/results/" + query['title'] + ".query.json.gz"

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
            print("WARNING: %s says: %s" % (current_app.config['FILLFORM'], errors))
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
    query = get_query(id)
    try:
        os.makedirs("instance/results/")
    except OSError:
        pass
    path_result = "instance/results/" + query['title'] + ".query.json.gz"

    # init CWBEngine
    from ccc.cwb import CWBEngine
    from ccc.anchors import anchor_query
    engine = CWBEngine(
        corpus_name=current_app.config['CORPUS_NAME'],
        lib_path=current_app.config['LIB_PATH'],
        registry_path=current_app.config['REGISTRY_PATH']
    )

    # run person_any once
    print(engine.cqp.Exec("/person_any[];"))

    # restrict to subcorpus
    # subcorpus = (
    #     "DEDUP=/region[tweet,a] :: (a.tweet_duplicate_status!='1') within tweet;"
    #     "DEDUP;"
    # )
    # engine.cqp.Exec(subcorpus)

    # set concordance settings
    concordance_settings = {
        'order': 'first',
        'cut_off': None,
        'p_show': ['lemma'],
        's_break': 'tweet',
        'match_strategy': 'longest'
    }

    query['concordance_settings'] = concordance_settings

    # create result
    query['result'] = anchor_query(engine,
                                   query['query'],
                                   query['anchors'],
                                   query['regions'],
                                   concordance_settings['s_break'],
                                   concordance_settings['p_show'],
                                   concordance_settings['match_strategy'])

    # dump result
    with gzip.open(path_result, 'wt') as f_out:
        json.dump(query, f_out, indent=4)

    # format result
    result = format_query_result(query)

    # render result
    return render_template('queries/show_result.html',
                           result=result)
