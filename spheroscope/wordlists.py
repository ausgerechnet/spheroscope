#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for)
from pandas import DataFrame
from pymagnitude import Magnitude

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import WordList

bp = Blueprint('wordlists', __name__, url_prefix='/wordlists')


def get_frequencies(cwb_id, words, p_att):

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)

    current_app.logger.info('getting frequency info for %d items' % (len(words)))
    freq = corpus.marginals(words, p_atts=[p_att])

    return freq


def get_similar_ones(cwb_id, words, p_att, number, min_freq=2):

    # similar ones
    current_app.logger.info('getting %d similar items for %d items' % (number, len(words)))
    corpus_config = read_config(cwb_id)
    if corpus_config['resources']['embeddings'] is None:
        current_app.logger.warning('no embeddings provided', 'warning')
        flash('no embeddings provided!')
    embeddings = Magnitude(corpus_config['resources']['embeddings'])
    similar = embeddings.most_similar(positive=words, topn=number)
    similar = DataFrame(index=[s[0] for s in similar], data={'similarity': [s[1] for s in similar]})

    # marginals
    freq_similar = get_frequencies(cwb_id, similar.index, p_att=p_att)
    freq_similar = freq_similar[['freq']]
    freq_similar.columns = ["frequency"]
    freq_similar = freq_similar.loc[freq_similar.frequency >= min_freq]  # drop hapaxes

    # merge
    freq_similar = freq_similar.join(similar)
    freq_similar = freq_similar.sort_values(by="frequency", ascending=False)

    return freq_similar


def get_defined_wordlists(cwb_id):

    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    defined_wordlists = corpus._wordlists_available()

    return defined_wordlists


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():

    if 'corpus' in session:
        cwb_id = session['corpus']['resources']['cwb_id']
        wordlists = WordList.query.filter_by(cwb_handle=cwb_id).order_by(WordList.name).all()
    else:
        cwb_id = None
        wordlists = WordList.query.order_by(WordList.name).all()

    corpus = {
        'wordlists': get_defined_wordlists(cwb_id),
        'cwb_id': cwb_id
    }

    return render_template('wordlists/index.html',
                           wordlists=wordlists,
                           corpus=corpus)


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
            cwb_handle=session['corpus']['resources']['cwb_id'],
            words="\n".join(sorted(list(set([
                w.lstrip().rstrip() for w in request.form['words'].split("\n")
            ])))),
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

        wordlist.delete()
        wordlist = WordList(
            id=id,
            user_id=g.user.id,
            cwb_handle=session['corpus']['resources']['cwb_id'],
            name=request.form['name'],
            words="\n".join(sorted(list(set([
                w.lstrip().rstrip() for w in request.form['words'].split("\n")
            ])))),
            p_att=request.form['p_att']
        )
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

    freq = freq.reset_index()[['item', 'frequency', 'similarity']]
    freq.columns = [c.capitalize() for c in freq.columns]

    # render result
    return render_template(
        'wordlists/similar.html',
        wordlist=wordlist,
        similar=freq.to_html(escape=False, border=0, index=False, justify='left',
                             classes=['table', 'is-striped', 'is-hoverable', 'is-narrow', 'sortable']),
        cwb_id=cwb_id
    )
