# from gensim.models.keyedvectors import KeyedVectors
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from spheroscope.auth import login_required
from spheroscope.db import get_db

bp = Blueprint('word_lists', __name__, url_prefix='/word-lists')

# EMBEDDINGS = KeyedVectors.load("/home/ausgerechnet/corpora/wectors/gensim/enTwitterWord2Vec")


def get_similar_tokens(tokens, number=20):
    # similar = EMBEDDINGS.most_similar(positive=tokens, topn=number)
    similar = [('test',), ('test',)]
    similar = "\n".join([s[0] for s in similar])
    return similar


@bp.route('/')
@login_required
def index():
    db = get_db()
    word_lists = db.execute(
        'SELECT wl.id, title, lemmata, created, author_id, username'
        ' FROM word_lists wl JOIN users u ON wl.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('word_lists/index.html', word_lists=word_lists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        lemmata = request.form['lemmata']
        error = None

        if not title:
            error = 'title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO word_lists (title, lemmata, author_id)'
                ' VALUES (?, ?, ?)',
                (title, lemmata, g.user['id'])
            )
            db.commit()
            return redirect(url_for('word_lists.index'))

    return render_template('word_lists/create.html')


def get_word_list(id, check_author=True):
    word_list = get_db().execute(
        'SELECT wl.id, title, lemmata, created, author_id, username'
        ' FROM word_lists wl JOIN users u ON wl.author_id = u.id'
        ' WHERE wl.id = ?',
        (id,)
    ).fetchone()

    if word_list is None:
        abort(404, "word list id {0} doesn't exist.".format(id))

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
            error = 'title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE word_lists SET title = ?, lemmata = ?'
                ' WHERE id = ?',
                (title, lemmata, id)
            )
            db.commit()
            return redirect(url_for('word_lists.index'))

    return render_template('word_lists/update.html', word_list=word_list)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_word_list(id)
    db = get_db()
    db.execute('DELETE FROM word_lists WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('word_lists.index'))


@bp.route('/<int:id>/show_similar_ones', methods=('GET', 'POST'))
@login_required
def show_similar_ones(id):
    word_list = get_word_list(id)
    lemmata = word_list['lemmata'].split("\n")
    similar_ones = get_similar_tokens(lemmata)
    return render_template('word_lists/show_similar_ones.html',
                           word_list=word_list, similar_ones=similar_ones)
