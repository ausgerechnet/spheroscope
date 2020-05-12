import os
from glob import glob
from pymagnitude import Magnitude

# flask
from flask import (
    Blueprint, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

# this app
from .auth import login_required
from .db import get_db
from .corpora import init_corpus


bp = Blueprint('wordlists', __name__, url_prefix='/wordlists')


def get_wordlist_from_db(id, check_author=True):

    wordlist = get_db().execute(
        'SELECT wl.id, name, words, p_att, modified, author_id, username'
        ' FROM wordlists wl JOIN users u ON wl.author_id = u.id'
        ' WHERE wl.id = ?',
        (id,)
    ).fetchone()

    if wordlist is None:
        abort(404, "word list id {0} doesn't exist.".format(id))

    if check_author and wordlist['author_id'] != g.user['id']:
        abort(403)

    return wordlist


def get_wordlists_from_db():

    wordlists = get_db().execute(
        'SELECT wl.id, name, words, modified, author_id, username'
        ' FROM wordlists wl JOIN users u ON wl.author_id = u.id'
        ' ORDER BY name ASC'
    ).fetchall()

    wordlists_new = list()
    for wl in wordlists:
        wl_new = dict(wl)
        wl_new['length'] = len(wl_new['words'].split("\n"))
        wordlists_new.append(wl_new)

    return wordlists_new


def get_wordlist_from_path(path):

    name = path.split("/")[-1].split(".")[0]
    if name.startswith("tag"):
        p_att = "pos_ark"
    else:
        p_att = "lemma"
    words = set()
    with open(path, "rt") as f:
        for line in f:
            words.add(line.rstrip())
    return {
        'name': name,
        'p_att': p_att,
        'words': "\n".join(words),
        # missing: id author_id modified
    }


def write_wordlist(wordlist, write_db=True, write_file=True):

    if write_db:
        current_app.logger.info(
            "writing wordlist %s to database" % wordlist['name']
        )
        db = get_db()
        db.execute(
            'INSERT INTO wordlists (name, words, p_att, author_id)'
            ' VALUES (?, ?, ?, ?)',
            (wordlist['name'], wordlist['words'],
             wordlist['p_att'], 1)
        )
        db.commit()

    if write_file:
        lib_path = current_app.config['LIB_PATH']
        path = os.path.join(lib_path, "wordlists", wordlist['name'] + ".txt")
        current_app.logger.info(
            "writing wordlist %s to %s" % (wordlist['name'], path)
        )
        with open(path, "wt") as f:
            f.write(wordlist['words'])


def delete_from_db(id):
    get_wordlist_from_db(id)
    db = get_db()
    db.execute('DELETE FROM wordlists WHERE id = ?', (id,))
    db.commit()


def wordlists_lib2db(lib_path):

    paths = glob(os.path.join(lib_path, 'wordlists', '*'))
    wordlists = dict()
    for p in paths:
        wlist = get_wordlist_from_path(p)
        write_wordlist(wlist, write_file=False)
        wordlists[wlist['name']] = wlist
    return wordlists


@bp.route('/')
@login_required
def index():
    wordlists = get_wordlists_from_db()
    return render_template('wordlists/index.html', wordlists=wordlists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        wordlist = {
            'name': request.form['name'],
            'words': request.form['words'],
            'p_att': request.form['p_att']
        }

        if not wordlist['name']:
            current_app.logger.error('name is required.')

        else:
            write_wordlist(wordlist)
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    wordlist = get_wordlist_from_db(id)
    if request.method == 'POST':
        wordlist = {
            'name': request.form['name'],
            'words': request.form['words'],
            'p_att': request.form['p_att']
        }

        if not wordlist['name']:
            current_app.logger.error('name is required.')

        else:
            delete_from_db(id)
            write_wordlist(wordlist)
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/update.html', wordlist=wordlist)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    delete_from_db(id)
    return redirect(url_for('wordlists.index'))


@bp.route('/<int:id>/frequencies', methods=['GET'])
@login_required
def show_frequencies(id):

    corpus = init_corpus(current_app.config)

    # get lemmas
    wordlist = get_wordlist_from_db(id)
    words = wordlist['words'].split("\n")
    words = [word.rstrip() for word in words]

    # get frequencies
    freq_original = corpus.marginals(words, p_att=wordlist['p_att'])
    freq_original.columns = ["frequency"]

    return render_template(
        'wordlists/show_frequencies.html',
        wordlist=wordlist,
        original=freq_original.to_html(escape=False)
    )


@bp.route('/<int:id>/similar', methods=['GET'])
@login_required
def show_similar_ones(id, number=200):

    corpus = init_corpus(current_app.config)

    # get lemmas
    wordlist = get_wordlist_from_db(id)
    words = wordlist['words'].split("\n")
    words = [word.rstrip() for word in words]

    # get similar ones
    current_app.logger.info(
        'getting %d similar items for %d items' % (number, len(words))
    )
    embeddings = Magnitude(current_app.config['EMBEDDINGS'])
    similar = embeddings.most_similar(positive=words, topn=number)
    similar_ones = [s[0] for s in similar]

    # get frequencies
    current_app.logger.info(
        'getting frequency info for %d items' % (len(similar_ones))
    )
    freq_similar = corpus.marginals(similar_ones, p_att=wordlist['p_att'])
    freq_similar.columns = ["frequency"]
    freq_similar['similarity'] = [s[1] for s in similar]
    freq_similar = freq_similar.loc[freq_similar.frequency > 1]
    freq_similar.sort_values(by="frequency", inplace=True, ascending=False)

    # render result
    return render_template(
        'wordlists/show_similar_ones.html',
        wordlist=wordlist,
        similar=freq_similar.to_html(escape=False)
    )
