import os
from glob import glob
from datetime import datetime

# ccc
from ccc.cwb import Corpus

# flask
from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g
)
from werkzeug.exceptions import abort

# this app
from .auth import login_required
from .db import get_db
from .corpora import read_config, init_corpus

bp = Blueprint('macros', __name__, url_prefix='/macros')


def read_from_path(path):
    """ reads a macro from specified path """

    if not os.path.isfile(path):
        abort(404, "macro '%s' doesn't exist." % path)

    # determine corpus from path
    corpus = path.split("/")[-3]

    # determine name from path
    name = path.split("/")[-1].split(".")[0]

    # get macro
    with open(path, "rt") as f:
        macro = f.read()

    # modified
    modified = datetime.utcfromtimestamp(os.path.getmtime(path))

    return {
        # id
        # user_id
        'modified': modified,
        'corpus': corpus,
        'name': name,
        'macro': macro
    }


def write(macro, write_db=True, write_file=True, update_modified=True):
    """ writes macro to database and instance folder """

    if update_modified:
        modified = datetime.now()
    else:
        modified = macro['modified']

    if write_db:
        current_app.logger.info(
            "writing macro '%s' to database" % macro['name']
        )
        db = get_db()
        if 'id' in macro:
            db.execute(
                'INSERT OR REPLACE INTO macros (id, user_id, modified, corpus, name, macro)'
                ' VALUES (?, ?, ?, ?, ?, ?)', (
                    macro['id'],
                    macro['user_id'],
                    modified,
                    macro['corpus'],
                    macro['name'],
                    macro['macro']
                )
            )
        else:
            db.execute(
                'INSERT INTO macros (user_id, modified, corpus, name, macro)'
                ' VALUES (?, ?, ?, ?, ?)', (
                    macro['user_id'],
                    modified,
                    macro['corpus'],
                    macro['name'],
                    macro['macro']
                )
            )
        db.commit()

    if write_file:

        # ensure directory for macros exists
        dir_out = os.path.join(
            current_app.instance_path, macro['corpus'], 'macros'
        )
        if not os.path.isdir(dir_out):
            os.makedirs(dir_out)

        # write
        path = os.path.join(
            dir_out, macro['name'] + ".txt"
        )
        current_app.logger.info(
            "writing macro '%s' to '%s'" % (macro['name'], path)
        )
        with open(path, "wt") as f:
            f.write(macro['macro'])


def read_from_db(ids=None):
    """ reads one or all macros from database """

    sql_cmd = (
        'SELECT m.id, user_id, modified, corpus, name, macro, username'
        ' FROM macros m JOIN users u ON m.user_id = u.id'
    )
    db = get_db()

    if ids is None:
        sql_cmd += ' ORDER BY name ASC'
        macros = db.execute(sql_cmd).fetchall()
    else:
        sql_cmd += ' WHERE m.id = ?'
        macros = list()
        for id in ids:
            macro = db.execute(sql_cmd, (id, )).fetchone()
            if macro is None:
                abort(404, "macro id %d doesn't exist." % id)
            macros.append(macro)

    # post-processing

    return macros


def delete(id, delete_db=True, delete_file=True):

    macro = read_from_db(ids=[id])[0]

    if delete_db:
        current_app.logger.info(
            "deleting macro '%s'" % macro['name']
        )
        db = get_db()
        db.execute('DELETE FROM macros WHERE id = ?', (id,))
        db.commit()

    if delete_file:
        # determine path
        dir_out = os.path.join(
            current_app.instance_path, macro['corpus'], 'macros'
        )
        path_del = os.path.join(
            dir_out, macro['name'] + ".txt"
        )
        # delete
        current_app.logger.warning(
            "deleting macro file '%s':" % (path_del)
        )
        if os.path.isfile(path_del):
            os.remove(path_del)
        else:
            current_app.logger.warning(
                "file does not exist, skipping delete request"
            )


def lib2db():
    """ reads all macros in library, writes to database """

    user_id = 1                 # master
    paths = glob(os.path.join('library', '*', 'macros', '*'))
    for p in paths:
        macro = read_from_path(p)
        macro['user_id'] = user_id
        write(macro, update_modified=False)


# frequencies
def get_frequencies(cwb_id, macro):

    # get frequencies
    current_app.logger.info(
        'getting frequency info for macro'
    )
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    corpus.subcorpus_from_query(macro['name'])
    freq = corpus.counts.matches()

    return freq


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    macros = read_from_db()
    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    cqp = corpus.start_cqp()
    defined_macros = cqp.Exec("show macro;").split("\n")
    cqp.__kill__()
    corpus = {
        'macros': defined_macros,
        'cwb_id': cwb_id
    }
    return render_template('macros/index.html',
                           macros=macros,
                           corpus=corpus)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    delete(id)
    return redirect(url_for('macros.index'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    # get corpus info (for s-atts)
    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    corpus = Corpus(cwb_id)
    a = corpus.attributes_available
    s_atts = list(
        a.name[([not b for b in a.annotation]) & (a.att == 's-Att')].values
    )
    corpus = {
        'cwb_id': cwb_id,
        's_atts': s_atts
    }

    if request.method == 'POST':
        macro = {
            'macro': request.form['macro'],
            'name': request.form['name'],
            'corpus': cwb_id,
            'user_id': g.user['id']
        }
        write(macro)
        return redirect(url_for('macros.index'))

    return render_template("macros/create.html",
                           corpus=corpus)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    macro = read_from_db(ids=[id])[0]

    # get corpus info (for s-atts)
    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    corpus = Corpus(cwb_id)
    a = corpus.attributes_available
    s_atts = list(
        a.name[([not b for b in a.annotation]) & (a.att == 's-Att')].values
    )
    corpus = {
        'cwb_id': cwb_id,
        's_atts': s_atts
    }
    if request.method == 'POST':
        macro = {
            'id': id,
            'macro': request.form['macro'],
            'name': request.form['name'],
            'corpus': cwb_id,
            'user_id': g.user['id']
        }
        write(macro)
        return redirect(url_for('macros.index'))

    return render_template("macros/update.html",
                           macro=macro,
                           corpus=corpus)


@bp.route('/<cwb_id>/<int:id>/frequencies', methods=['GET'])
@login_required
def show_frequencies(cwb_id, id):

    # get macro
    macro = read_from_db([id])[0]

    # get frequencies
    freq = get_frequencies(
        cwb_id, macro['macro']
    )

    return render_template(
        'macros/show_frequencies.html',
        frequencies=freq.to_html(escape=False),
        cwb_id=cwb_id
    )
