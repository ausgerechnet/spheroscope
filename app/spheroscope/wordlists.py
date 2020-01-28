from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort
from pymagnitude import Magnitude

from spheroscope.auth import login_required
from spheroscope.db import get_db


bp = Blueprint('wordlists', __name__, url_prefix='/wordlists')


def get_wordlist(id, check_author=True):
    wordlist = get_db().execute(
        'SELECT wl.id, title, words, created, author_id, username'
        ' FROM wordlists wl JOIN users u ON wl.author_id = u.id'
        ' WHERE wl.id = ?',
        (id,)
    ).fetchone()

    if wordlist is None:
        abort(404, "word list id {0} doesn't exist.".format(id))

    if check_author and wordlist['author_id'] != g.user['id']:
        abort(403)

    return wordlist


@bp.route('/')
@login_required
def index():
    db = get_db()
    wordlists = db.execute(
        'SELECT wl.id, title, words, created, author_id, username'
        ' FROM wordlists wl JOIN users u ON wl.author_id = u.id'
        ' ORDER BY title ASC'
    ).fetchall()
    return render_template('wordlists/index.html', wordlists=wordlists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        words = request.form['words']
        error = None

        if not title:
            error = 'title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO wordlists (title, words, author_id)'
                ' VALUES (?, ?, ?)',
                (title, words, g.user['id'])
            )
            db.commit()
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    wordlist = get_wordlist(id)
    if request.method == 'POST':
        title = request.form['title']
        words = request.form['words']
        error = None

        if not title:
            error = 'title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE wordlists SET title = ?, words = ?'
                ' WHERE id = ?',
                (title, words, id)
            )
            db.commit()
            return redirect(url_for('wordlists.index'))

    return render_template('wordlists/update.html', wordlist=wordlist)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_wordlist(id)
    db = get_db()
    db.execute('DELETE FROM wordlists WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('wordlists.index'))


@bp.route('/<int:id>/frequencies', methods=('GET', 'POST'))
@login_required
def show_frequencies(id):

    p_att = "lemma"
    engine = current_app.config['ENGINE']

    # get lemmas
    wordlist = get_wordlist(id)
    words = wordlist['words'].split("\n")
    words = [word.rstrip() for word in words]

    # get frequencies
    freq_original = engine.item_freq(words, p_att=p_att)
    freq_original.columns = ["frequency"]

    return render_template(
        'wordlists/show_frequencies.html',
        wordlist=wordlist,
        original=freq_original.to_html(escape=False)
    )


@bp.route('/<int:id>/similar', methods=('GET', 'POST'))
@login_required
def show_similar_ones(id):

    p_att = "lemma"
    engine = current_app.config['ENGINE']

    # get lemmas
    wordlist = get_wordlist(id)
    words = wordlist['words'].split("\n")
    words = [word.rstrip() for word in words]

    # get frequencies
    freq_original = engine.item_freq(words, p_att=p_att)
    freq_original.columns = ["frequency"]

    # get similar ones
    number = 200
    embeddings = Magnitude(current_app.config['EMBEDDINGS'])
    similar = embeddings.most_similar(positive=words, topn=number)
    similar_ones = [s[0] for s in similar]

    # get frequencies
    freq_similar = engine.item_freq(similar_ones, p_att=p_att)
    freq_similar.columns = ["frequency"]
    freq_similar['similarity'] = [s[1] for s in similar]
    freq_similar = freq_similar.loc[freq_similar.frequency > 1]
    freq_similar.sort_values(by="frequency", inplace=True, ascending=False)

    # render result
    return render_template(
        'wordlists/show_similar_ones.html',
        wordlist=wordlist,
        similar=freq_similar.to_html(escape=False),
        original=freq_original.to_html(escape=False)
    )
