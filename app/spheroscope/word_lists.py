from gensim.models.keyedvectors import KeyedVectors
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from spheroscope.auth import login_required
from spheroscope.db import get_db

bp = Blueprint('word_list', __name__)

EMBEDDINGS = KeyedVectors.load("/home/ausgerechnet/corpora/wectors/gensim/enTwitterWord2Vec")


def get_similar_tokens(tokens, number=20):
    similar = EMBEDDINGS.most_similar(positive=tokens, topn=number)
    similar = "\n".join([s[0] for s in similar])
    return similar


@bp.route('/')
def index():
    db = get_db()
    word_list = db.execute(
        'SELECT wl.id, title, lemmata, created, author_id, username'
        ' FROM word_list wl JOIN user u ON wl.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('word_list/index.html', word_lists=word_list)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        lemmata = request.form['lemmata']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO word_list (title, lemmata, author_id)'
                ' VALUES (?, ?, ?)',
                (title, lemmata, g.user['id'])
            )
            db.commit()
            return redirect(url_for('word_list.index'))

    return render_template('word_list/create.html')


def get_word_list(id, check_author=True):
    word_list = get_db().execute(
        'SELECT wl.id, title, lemmata, created, author_id, username'
        ' FROM word_list wl JOIN user u ON wl.author_id = u.id'
        ' WHERE wl.id = ?',
        (id,)
    ).fetchone()

    if word_list is None:
        abort(404, "word_list id {0} doesn't exist.".format(id))

    if check_author and word_list['author_id'] != g.user['id']:
        abort(403)

    return word_list


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    word_list = get_word_list(id)
    if request.method == 'POST':
        title = request.form['title']
        lemmata = request.form['lemmata']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE word_list SET title = ?, lemmata = ?'
                ' WHERE id = ?',
                (title, lemmata, id)
            )
            db.commit()
            return redirect(url_for('word_list.index'))

    return render_template('word_list/update.html', word_list=word_list)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_word_list(id)
    db = get_db()
    db.execute('DELETE FROM word_list WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('word_list.index'))


@bp.route('/<int:id>/show_similar_ones', methods=('GET', 'POST'))
@login_required
def show_similar_ones(id):
    word_list = get_word_list(id)
    lemmata = word_list['lemmata'].split("\r\n")
    similar_ones = get_similar_tokens(lemmata)
    return render_template('word_list/show_similar_ones.html', word_list=word_list, similar_ones=similar_ones)
