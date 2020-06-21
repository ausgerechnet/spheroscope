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


def read_wordlist_from_db(id, check_author=False):

    wordlist = get_db().execute(
        'SELECT wl.id, name, words, corpus, p_att, modified, author_id, username'
        ' FROM wordlists wl JOIN users u ON wl.author_id = u.id'
        ' WHERE wl.id = ?',
        (id,)
    ).fetchone()

    if wordlist is None:
        abort(404, "word list id {0} doesn't exist.".format(id))

    if check_author and wordlist['author_id'] != g.user['id']:
        abort(403)

    return wordlist


def read_wordlists_from_db():

    wordlists = get_db().execute(
        'SELECT wl.id, name, words, corpus, modified, author_id, username'
        ' FROM wordlists wl JOIN users u ON wl.author_id = u.id'
        ' ORDER BY name ASC'
    ).fetchall()

    wordlists_new = list()
    for wl in wordlists:
        wl_new = dict(wl)
        wl_new['length'] = len(wl_new['words'].split("\n"))
        wordlists_new.append(wl_new)

    return wordlists_new


def read_wordlist_from_path(path):

    # determine p-attribute from file name
    name = path.split("/")[-1].split(".")[0]
    if name.startswith("tag"):
        p_att = "pos_ark"
    else:
        p_att = "lemma"

    # determine corpus
    corpus = path.split("/")[-3]

    # get all words
    words = set()
    with open(path, "rt") as f:
        for line in f:
            words.add(line.rstrip())
    return {
        'name': name,
        'p_att': p_att,
        'words': "\n".join(words),
        'corpus': corpus
    }


def write_wordlist(wordlist, write_db=True, write_file=True):
    """ writes to database and instance folder """
    if write_db:
        current_app.logger.info(
            "writing wordlist %s to database" % wordlist['name']
        )
        db = get_db()
        db.execute(
            'INSERT INTO wordlists (name, words, p_att, corpus, author_id)'
            ' VALUES (?, ?, ?, ?, ?)',
            (wordlist['name'], wordlist['words'],
             wordlist['p_att'], wordlist['corpus'], 1)  # TODO determine user
        )
        db.commit()

    if write_file:
        # determine path
        dir_out = os.path.join('library', wordlist['corpus'], "wordlists")
        if not os.path.isdir(dir_out):
            os.makedirs(dir_out)
        path = os.path.join(dir_out, wordlist['name'] + ".txt")
        # write
        current_app.logger.info(
            "writing wordlist %s to %s" % (wordlist['name'], path)
        )
        with open(path, "wt") as f:
            f.write(wordlist['words'])


def delete(id, delete_db=True, delete_file=True):

    wordlist = read_wordlist_from_db(id)

    if delete_db:
        current_app.logger.warning(
            "removing wordlist %s" % wordlist['name']
        )
        db = get_db()
        db.execute('DELETE FROM wordlists WHERE id = ?', (id,))
        db.commit()

    if delete_file:
        # determine path
        dir_out = os.path.join('library', wordlist['corpus'])
        path = os.path.join(dir_out, "wordlists", wordlist['name'] + ".txt")
        # delete
        current_app.logger.warning(
            "removing wordlist file %s:" % (path)
        )
        print(path)
        # os.remove(path)


# copy from master library
def lib2db():

    import os
    print(os.getcwd())
    print(os.path.join('library', '*', 'wordlists', '*'))
    paths = glob(os.path.join('library', '*', 'wordlists', '*'))
    # current_app.logger.debug(paths)
    for p in paths:
        wlist = read_wordlist_from_path(p)
        write_wordlist(wlist, write_file=False)


# frequencies
def get_frequencies(words, p_att):

    # get frequencies
    current_app.logger.info(
        'getting frequency info for %d items' % (len(words))
    )
    corpus = init_corpus(current_app.config)
    freq = corpus.marginals(words, p_att=p_att)

    return freq


def get_similar_ones(words, p_att, number):

    # get similar ones
    current_app.logger.info(
        'getting %d similar items for %d items' % (number, len(words))
    )
    embeddings = Magnitude(current_app.config['EMBEDDINGS'])
    similar = embeddings.most_similar(positive=words, topn=number)
    similar_ones = [s[0] for s in similar]

    # get frequencies
    current_app.logger.info(
        'getting frequency info for %d items' % (len(words))
    )
    corpus = init_corpus(current_app.config)
    freq_similar = corpus.marginals(similar_ones, p_att=p_att)
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
    wordlists = read_wordlists_from_db()
    return render_template('wordlists/index.html', wordlists=wordlists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        wordlist = {
            'name': request.form['name'],
            'words': request.form['words'],
            'p_att': request.form['p_att'],
            'corpus': current_app.config['corpus']
        }

        if not wordlist['name']:
            current_app.logger.error('name is required.')

        else:
            write_wordlist(wordlist)
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/create.html')


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    delete(id)
    return redirect(url_for('wordlists.index'))


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    # TODO: give same id
    wordlist = read_wordlist_from_db(id)

    if request.method == 'POST':
        wordlist = {
            'name': request.form['name'],
            'words': request.form['words'],
            'p_att': request.form['p_att'],
            'corpus': current_app.config['CORPUS1']
        }
        print(wordlist)

        if not wordlist['name']:
            current_app.logger.error('name is required.')

        else:
            delete(id)
            write_wordlist(wordlist)
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/update.html', wordlist=wordlist)


@bp.route('/<int:id>/frequencies', methods=['GET'])
@login_required
def show_frequencies(id):

    # get lemmas
    wordlist = read_wordlist_from_db(id)

    # format lemmas
    words = wordlist['words'].split("\n")
    words = [word.rstrip() for word in words]

    # get frequencies
    freq = get_frequencies(words, wordlist['p_att'])

    return render_template(
        'wordlists/show_frequencies.html',
        wordlist=wordlist,
        original=freq.to_html(escape=False)
    )


@bp.route('/<int:id>/similar', methods=['GET'])
@login_required
def show_similar_ones(id, number=200):

    # get lemmas
    wordlist = read_wordlist_from_db(id)

    # format lemmas
    words = wordlist['words'].split("\n")
    words = [word.rstrip() for word in words]

    # get frequencies
    freq = get_similar_ones(words, wordlist['p_att'], number)

    # render result
    return render_template(
        'wordlists/show_similar_ones.html',
        wordlist=wordlist,
        similar=freq.to_html(escape=False)
    )
