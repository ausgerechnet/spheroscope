import os
from glob import glob
from datetime import datetime

# ccc
from ccc.cwb import Corpus

# requirements
from pymagnitude import Magnitude

# flask
from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g
)
from werkzeug.exceptions import abort

# this app
from .auth import login_required
from .db import get_db
from .corpora import init_corpus, read_config

bp = Blueprint('wordlists', __name__, url_prefix='/wordlists')


def read_from_path(path):
    """ reads a wordlist from specified path """

    if not os.path.isfile(path):
        abort(404, "word list '%s' doesn't exist." % path)

    # determine corpus from path
    corpus = path.split("/")[-3]

    # determine name from path
    name = path.split("/")[-1].split(".")[0]

    # determine p-attribute from name
    if name.startswith("tag"):
        p_att = "pos_ark"
    else:
        p_att = "lemma"

    # get all words
    words = set()
    with open(path, "rt") as f:
        for line in f:
            words.add(line.rstrip())

    # modified
    modified = datetime.utcfromtimestamp(os.path.getmtime(path))

    return {
        # id
        # user_id
        'modified': modified,
        'corpus': corpus,
        'name': name,
        'words': words,
        'p_att': p_att,
        'length': len(words)
    }


def write(wordlist, write_db=True, write_file=True, update_modified=True):
    """ writes wordlist to database and instance folder """

    if update_modified:
        modified = datetime.now()
    else:
        modified = wordlist['modified']

    if write_db:
        current_app.logger.info(
            "writing wordlist '%s' to database" % wordlist['name']
        )
        db = get_db()
        if 'id' in wordlist:
            db.execute(
                'INSERT INTO wordlists '
                '(id, user_id, modified, corpus, name, words, p_att)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)', (
                    wordlist['id'],
                    wordlist['user_id'],
                    modified,
                    wordlist['corpus'],
                    wordlist['name'],
                    "\n".join(wordlist['words']),
                    wordlist['p_att']
                )
            )
        else:
            db.execute(
                'INSERT INTO wordlists (user_id, modified, corpus, name, words, p_att)'
                ' VALUES (?, ?, ?, ?, ?, ?)', (
                    wordlist['user_id'],
                    modified,
                    wordlist['corpus'],
                    wordlist['name'],
                    "\n".join(wordlist['words']),
                    wordlist['p_att']
                )
            )
        db.commit()

    if write_file:

        # ensure directory for wordlists exists
        dir_out = os.path.join(
            current_app.instance_path, wordlist['corpus'], 'wordlists'
        )
        if not os.path.isdir(dir_out):
            os.makedirs(dir_out)
        path = os.path.join(
            dir_out, wordlist['name'] + ".txt"
        )

        # write
        current_app.logger.info(
            "writing wordlist '%s' to '%s'" % (wordlist['name'], path)
        )
        with open(path, "wt") as f:
            f.write("\n".join(wordlist['words']))


def read_from_db(ids=None):
    """ reads one or all wordlists from database """

    sql_cmd = (
        'SELECT wl.id, user_id, modified, corpus, name, words, p_att, username'
        ' FROM wordlists wl JOIN users u ON wl.user_id = u.id'
    )
    db = get_db()

    if ids is None:
        sql_cmd += ' ORDER BY name ASC'
        wordlists = db.execute(sql_cmd).fetchall()
    else:
        sql_cmd += ' WHERE wl.id = ?'
        wordlists = list()
        for id in ids:
            wordlist = db.execute(sql_cmd, (id, )).fetchone()
            if wordlist is None:
                abort(404, "word list id %d doesn't exist." % id)
            wordlists.append(wordlist)

    # post-processing
    wordlists_dicts = list()
    for wl in wordlists:
        wl_dict = dict(wl)
        wl_dict['words'] = set(wl['words'].split("\n"))
        wl_dict['length'] = len(wl_dict['words'])
        wordlists_dicts.append(wl_dict)

    return wordlists_dicts


def delete(id, delete_db=True, delete_file=True):

    wordlist = read_from_db(ids=[id])[0]

    if delete_db:
        current_app.logger.info(
            "deleting wordlist '%s'" % wordlist['name']
        )
        db = get_db()
        db.execute('DELETE FROM wordlists WHERE id = ?', (id,))
        db.commit()

    if delete_file:
        # determine path
        dir_out = os.path.join(
            current_app.instance_path, wordlist['corpus'], 'wordlists'
        )
        path_del = os.path.join(
            dir_out, wordlist['name'] + ".txt"
        )
        # delete
        current_app.logger.warning(
            "deleting wordlist file '%s':" % (path_del)
        )
        if os.path.isfile(path_del):
            os.remove(path_del)
        else:
            current_app.logger.warning(
                "file does not exist, skipping delete request"
            )


def lib2db():
    """ reads all wordlists in library, writes to database """

    user_id = 1                 # master
    paths = glob(os.path.join('library', '*', 'wordlists', '*'))
    for p in paths:
        wlist = read_from_path(p)
        wlist['user_id'] = user_id
        write(wlist, update_modified=False)


# frequencies
def get_frequencies(cwb_id, words, p_att):

    # get frequencies
    current_app.logger.info(
        'getting frequency info for %d items' % (len(words))
    )
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    freq = corpus.counts.marginals(words, p_att=p_att)

    return freq


def get_similar_ones(cwb_id, words, p_att, number):

    words = list(words)
    corpus_config = read_config(cwb_id)

    # get resources
    embeddings = Magnitude(corpus_config['resources']['embeddings'])
    corpus = init_corpus(corpus_config)

    # get similar ones
    current_app.logger.info(
        'getting %d similar items for %d items' % (number, len(words))
    )
    similar = embeddings.most_similar(positive=words, topn=number)
    similar_ones = [s[0] for s in similar]

    # get frequencies
    current_app.logger.info(
        'getting frequency info for %d items' % (len(similar_ones))
    )
    freq_similar = corpus.counts.marginals(similar_ones, p_att=p_att)
    freq_similar.columns = ["frequency"]

    # attach similarity score
    freq_similar['similarity'] = [s[1] for s in similar]
    freq_similar = freq_similar.loc[freq_similar.frequency > 1]
    freq_similar = freq_similar.sort_values(by="frequency", ascending=False)

    return freq_similar


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    wordlists = read_from_db()
    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    return render_template('wordlists/index.html', wordlists=wordlists, cwb_id=cwb_id)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    delete(id)
    return redirect(url_for('wordlists.index'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    # get corpus info (for p-atts)
    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    corpus = Corpus(cwb_id)
    a = corpus.attributes_available
    p_atts = list(a.name[a.att == 'p-Att'].values)
    corpus = {
        'cwb_id': cwb_id,
        'p_atts': p_atts
    }

    # get user input
    if request.method == 'POST':

        wordlist = {
            'user_id': g.user['id'],
            'name': request.form['name'],
            'words': request.form['words'],
            'p_att': request.form['p_att'],
            'corpus': cwb_id
        }

        if not wordlist['name']:
            current_app.logger.error('name is required.')

        else:
            write(wordlist)
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/create.html', corpus=corpus)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    wordlist = read_from_db([id])[0]
    wordlist['words'] = "\n".join(wordlist['words'])

    cwb_id = current_app.config['CORPUS']['resources']['cwb_id']
    corpus = Corpus(cwb_id)
    a = corpus.attributes_available
    p_atts = list(a.name[a.att == 'p-Att'].values)
    corpus = {
        'cwb_id': cwb_id,
        'p_atts': p_atts
    }

    if request.method == 'POST':

        wordlist = {
            'id': id,
            'user_id': g.user['id'],
            'corpus': wordlist['corpus'],
            'name': request.form['name'],
            'words': set([w.rstrip() for w in request.form['words'].split("\n")]),
            'p_att': request.form['p_att'],
        }

        if not wordlist['name']:
            current_app.logger.error('name is required.')

        else:
            delete(id)
            write(wordlist)
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/update.html',
                           wordlist=wordlist,
                           corpus=corpus)


@bp.route('/<cwb_id>/<int:id>/frequencies', methods=['GET'])
@login_required
def show_frequencies(cwb_id, id):

    # get lemmas
    wordlist = read_from_db([id])[0]

    # get frequencies
    freq = get_frequencies(
        cwb_id, wordlist['words'], wordlist['p_att']
    )

    return render_template(
        'wordlists/show_frequencies.html',
        wordlist=wordlist,
        original=freq.to_html(escape=False),
        cwb_id=cwb_id
    )


@bp.route('/<cwb_id>/<int:id>/similar', methods=['GET'])
@login_required
def show_similar_ones(cwb_id, id, number=200):

    # get wordlist
    wordlist = read_from_db([id])[0]

    # get similar ones with frequencies
    freq = get_similar_ones(cwb_id,
                            wordlist['words'],
                            wordlist['p_att'],
                            number)

    # render result
    return render_template(
        'wordlists/show_similar_ones.html',
        wordlist=wordlist,
        similar=freq.to_html(escape=False),
        cwb_id=cwb_id
    )
