import json
import os
from datetime import datetime
from glob import glob
import ast
from .utils import generate_idx

# flask
from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort
# from flask.cli import with_appcontext
# import click

# this app
from .auth import login_required
from .db import get_db
from .corpora import read_config, init_corpus


bp = Blueprint('queries', __name__, url_prefix='/queries')


def read_from_path(path):
    """ reads a query from specified path """

    try:
        with open(path, "rt") as f:
            query = json.loads(f.read())

        # determine corpus from path
        query['corpus'] = path.split("/")[-3]

    except json.JSONDecodeError:
        abort(404, "JSON error in '%s'" % path)

    return query


def write(query, write_db=True, write_file=True, update_modified=True):

    if update_modified:
        modified = datetime.now()
    else:
        modified = query['modified']

    if write_db:
        current_app.logger.info(
            "writing query '%s' to database" % query['name']
        )
        db = get_db()
        if 'id' in query:
            db.execute(
                "INSERT INTO queries"
                " (id, user_id, modified, corpus, name, query,"
                " anchors, regions, pattern)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", (
                    query['id'],
                    query['user_id'],
                    modified,
                    query['corpus'],
                    query['name'],
                    query['query'],
                    json.dumps(query['anchors']),
                    json.dumps(query['regions']),
                    query['pattern']
                )
            )
        else:
            db.execute(
                "INSERT INTO queries "
                "(user_id, modified, corpus, name, query, anchors, regions, pattern) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (
                    query['user_id'],
                    modified,
                    query['corpus'],
                    query['name'],
                    query['query'],
                    json.dumps(query['anchors']),
                    json.dumps(query['regions']),
                    query['pattern']
                )
            )
        db.commit()

    if write_file:

        # ensure directory for query exists
        dir_out = os.path.join(
            current_app.instance_path, query['corpus'], 'queries'
        )
        if not os.path.isdir(dir_out):
            os.makedirs(dir_out)
        path = os.path.join(
            dir_out, query['name'] + ".query"
        )

        # write
        current_app.logger.info(
            "writing query '%s' to '%s'" % (query['name'], path)
        )
        with open(path, "wt") as f:
            json.dump(query, f, indent=4)


def read_from_db(ids=None, pattern=None):

    sql_cmd = (
        'SELECT qu.id, user_id, modified, corpus, name,'
        ' query, anchors, regions, pattern'
        ' FROM queries qu JOIN users u ON qu.user_id = u.id'
    )
    db = get_db()

    if ids is None:
        if pattern is not None:
            sql_cmd += "WHERE pattern = ?"
            queries = db.execute(sql_cmd, (pattern,)).fetchall()
        else:
            sql_cmd += ' ORDER BY name ASC'
            queries = db.execute(sql_cmd).fetchall()
    else:
        sql_cmd += ' WHERE qu.id = ?'
        queries = list()
        for id in ids:
            query = db.execute(sql_cmd, (id, )).fetchone()
            if query is None:
                abort(404, "query id %d doesn't exist" % id)
            queries.append(query)

    # format result
    queries_format = list()
    for query in queries:
        query = dict(query)
        query['anchors'] = json.loads(query['anchors'])
        query['regions'] = json.loads(query['regions'])
        queries_format.append(query)

    return queries_format


def delete(id, delete_db=True, delete_file=True):

    query = read_from_db(id)

    if delete_db:
        current_app.logger.info(
            "deleting query '%s'" % query['name']
        )
        db = get_db()
        db.execute('DELETE FROM queries WHERE id = ?', (id,))
        db.commit()

    if delete_file:
        # determine path
        dir_out = os.path.join(
            current_app.instance_path, query['corpus'], 'queries'
        )
        path_del = os.path.join(
            dir_out, query['name'] + ".query"
        )
        # delete
        current_app.logger.warning(
            "deleting query file '%s':" % (path_del)
        )
        if os.path.isfile(path_del):
            os.remove(path_del)
        else:
            current_app.logger.warning(
                "file does not exist, skipping delete request"
            )


def lib2db():
    """ reads all queries in library, writes to database """

    user_id = 1                 # master
    paths = glob(os.path.join('library', '*', 'queries', '*'))
    for p in paths:
        query = read_from_path(p)
        query['user_id'] = user_id
        if query is not None:
            write(query)


def run(id, cwb_id):

    # get query
    query = dict(read_from_db([id])[0])

    # determine active parameters from config
    corpus_config = read_config(cwb_id)
    for item, value in corpus_config.items('query'):
        query[item] = value

    # translate corrections
    corrections = dict()
    for cor in query['anchors']:
        corrections[cor[0]] = cor[1]
    query['corrections'] = corrections

    # display parameters
    for item, value in corpus_config.items('display'):
        query[item] = value
    query['s_show'] = ast.literal_eval(query['s_show'])
    query['p_show'] = ast.literal_eval(query['p_show'])

    # translate regions
    regions = list()
    for region in query['regions']:
        regions.append((region[0], region[1]))
    query['regions'] = regions

    # run query
    corpus = init_corpus(corpus_config)
    current_app.logger.info('running query')
    result = corpus.query(query=query['query'],
                          context=query.get('context', None),
                          s_context=query.get('s_context', None),
                          corrections=query['corrections'],
                          match_strategy=query['match_strategy'])

    conc = corpus.concordance(result)
    result = conc.lines(
        form='extended',
        p_show=query['p_show'],
        s_show=query['s_show'],
        p_text=query['p_text'],
        p_slots=query['p_slots'],
        regions=query['regions'],
        order='first',
        cut_off=None
    )

    result_parameters = [query[key] for key in query.keys() if key not in [
        'id', 'user_id', 'modified', 'pattern'
    ]]
    param = generate_idx(result_parameters, prefix='param-', length=10)

    # determine path to result
    dir_result = os.path.join(current_app.instance_path, cwb_id, 'matches', param)
    if not os.path.isdir(dir_result):
        os.makedirs(dir_result)
    path_result = os.path.join(dir_result, query['name'] + ".tsv.gz")

    # save result
    current_app.logger.info('saving result')
    result.to_csv(path_result, sep="\t")

    return result


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    queries = read_from_db()
    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    return render_template('queries/index.html', queries=queries, cwb_id=cwb_id)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        query = {
            'name': request.form['name'],
            'query': request.form['query'],
            'pattern': request.form['pattern'],
            'anchors': json.loads(request.form['anchors'].replace(
                "None", "null"
            ).replace("\'", "\"")),
            'regions': json.loads(request.form['regions'].replace(
                "None", "null"
            ).replace("\'", "\""))
        }

        if not query['name']:
            current_app.logger.error('name is required.')

        else:
            write(query)
            return redirect(url_for('queries.index'))

    return render_template('queries/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    query = read_from_db([id])[0]
    if request.method == 'POST':
        query = {
            'name': request.form['name'],
            'query': request.form['query'],
            'pattern': request.form['pattern'],
            'anchors': json.loads(request.form['anchors'].replace(
                "None", "null"
            ).replace("\'", "\"")),
            'regions': json.loads(request.form['regions'].replace(
                "None", "null"
            ).replace("\'", "\""))
        }

        if not query['name']:
            current_app.logger.error('name is required.')

        else:
            write(query)
            return redirect(url_for('queries.index'))

    return render_template('queries/update.html', query=query)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    delete(id)
    return redirect(url_for('queries.index'))


@bp.route('/<cwb_id>/<int:id>/run', methods=('GET', 'POST'))
@login_required
def run_cmd(cwb_id, id, show=True):

    result = run(id, cwb_id)
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
