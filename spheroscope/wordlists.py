#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from pymagnitude import Magnitude

from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g, session
)

from .auth import login_required
from .database import WordList
from .corpora import init_corpus, read_config

bp = Blueprint('wordlists', __name__, url_prefix='/wordlists')


def get_frequencies(cwb_id, words, p_att):

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    current_app.logger.info('getting frequency info for %d items' % (len(words)))
    freq = corpus.marginals(words, p_att=p_att)

    return freq


def get_similar_ones(cwb_id, words, p_att, number):

    # similar ones
    current_app.logger.info(
        'getting %d similar items for %d items' % (number, len(words))
    )
    corpus_config = read_config(cwb_id)
    embeddings = Magnitude(corpus_config['resources']['embeddings'])
    similar = embeddings.most_similar(positive=words, topn=number)
    similar_ones = [s[0] for s in similar]

    # marginals
    freq_similar = get_frequencies(cwb_id, similar_ones, p_att=p_att)
    freq_similar.columns = ["frequency"]

    # attach similarity score
    freq_similar['similarity'] = [s[1] for s in similar]
    freq_similar = freq_similar.loc[freq_similar.frequency > 1]  # drop hapaxes
    freq_similar = freq_similar.sort_values(by="frequency", ascending=False)

    return freq_similar


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    wordlists = WordList.query.order_by(WordList.name).all()
    return render_template('wordlists/index.html',
                           wordlists=wordlists)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    wl = WordList.query.filter_by(id=id).first()
    wl.delete()
    return redirect(url_for('wordlists.index'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    # get corpus info (for p-atts and path)
    cwb_id = session['corpus']['resources']['cwb_id']
    corpus_config = session['corpus']
    corpus = init_corpus(corpus_config)
    attributes = corpus.attributes_available
    p_atts = list(attributes['attribute'][attributes['type'] == 'p-Att'].values)
    corpus = {
        'cwb_id': cwb_id,
        'p_atts': p_atts
    }

    if request.method == 'POST':

        wordlist = WordList(
            user_id=g.user.id,
            name=request.form['name'],
            words="\n".join(sorted(list(set([
                w.lstrip().rstrip() for w in request.form['words'].split("\n")
            ])))),
            path=os.path.join(
                current_app.instance_path, cwb_id, 'wordlists',
                request.form['name'] + ".txt"
            ),
            p_att=request.form['p_att']
        )
        wordlist.write()

        return redirect(url_for('wordlists.index'))

    return render_template('wordlists/create.html',
                           corpus=corpus)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    wordlist = WordList.query.filter_by(id=id).first()

    # get corpus info (for p-atts and frequencies)
    cwb_id = session['corpus']['resources']['cwb_id']
    corpus_config = session['corpus']
    corpus = init_corpus(corpus_config)
    attributes = corpus.attributes_available
    p_atts = list(attributes['attribute'][attributes['type'] == 'p-Att'].values)
    corpus = {
        'cwb_id': cwb_id,
        'p_atts': p_atts
    }

    if request.method == 'POST':

        wordlist = WordList(
            id=id,
            user_id=g.user.id,
            name=request.form['name'],
            words="\n".join(sorted(list(set([
                w.lstrip().rstrip() for w in request.form['words'].split("\n")
            ])))),
            path=wordlist.path,
            p_att=request.form['p_att']
        )

        wordlist.delete()
        wordlist.write()
        return redirect(url_for('wordlists.index'))

    return render_template('wordlists/update.html',
                           wordlist=wordlist,
                           corpus=corpus)


@bp.route('/<int:id>/frequencies', methods=['GET'])
@login_required
def frequencies(id):

    wordlist = WordList.query.filter_by(id=id).first()
    cwb_id = session['corpus']['resources']['cwb_id']

    # get frequencies
    freq = get_frequencies(
        cwb_id,
        wordlist.words.split("\n"),
        wordlist.p_att
    )

    return render_template(
        'wordlists/frequencies.html',
        wordlist=wordlist,
        frequencies=freq,
        cwb_id=cwb_id
    )


@bp.route('/<int:id>/similar', methods=['GET'])
@login_required
def similar(id, number=200):

    wordlist = WordList.query.filter_by(id=id).first()
    cwb_id = session['corpus']['resources']['cwb_id']

    # get similar ones with frequencies
    freq = get_similar_ones(
        cwb_id,
        wordlist.words.split("\n"),
        wordlist.p_att,
        number
    )

    # render result
    return render_template(
        'wordlists/similar.html',
        wordlist=wordlist,
        similar=freq.to_html(escape=False),
        cwb_id=cwb_id
    )
