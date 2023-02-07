#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import yaml
from ccc.cwb import Corpora, Corpus
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session)

from .auth import login_required

bp = Blueprint('corpora', __name__, url_prefix='/corpora')


def load_default():

    default_path = os.path.join(current_app.instance_path, 'corpus_defaults.yaml')
    corpus_config = yaml.load(
        open(default_path, "rt").read(), Loader=yaml.FullLoader
    )

    return corpus_config


def read_config(cwb_id=None, init=False):

    if cwb_id is None:
        init = True

    if init:

        # load defaults
        default = load_default()

        # get default cwb_id if necessary
        cwb_id = default['resources']['cwb_id'] if cwb_id is None else cwb_id

        # init corpus specific data directory if necessary
        corpus_dir = os.path.join(current_app.instance_path, cwb_id)
        os.makedirs(corpus_dir, exist_ok=True)

        # load or create corpus config
        cfg_path = os.path.join(corpus_dir, cwb_id + '.yaml')
        if os.path.isfile(cfg_path):
            corpus_config = yaml.load(open(cfg_path, "rt").read(), Loader=yaml.FullLoader)
        else:
            # set defaults
            corpus_config = default
            corpus_config['resources']['cwb_id'] = cwb_id
            corpus_config['resources']['lib_path'] = corpus_dir
            corpus_config['resources']['embeddings'] = current_app.config['EMBEDDINGS'].get(cwb_id, None)
            # save to appropriate place
            with open(cfg_path, "wt") as f:
                yaml.dump(corpus_config, f)

    else:
        # init corpus specific data directory if necessary
        corpus_dir = os.path.join(current_app.instance_path, cwb_id)
        cfg_path = os.path.join(corpus_dir, cwb_id + '.yaml')

        # read or init settings
        if os.path.isfile(cfg_path):
            corpus_config = yaml.load(open(cfg_path, "rt").read(), Loader=yaml.FullLoader)
        else:
            # load default and save to appropriate place
            corpus_config = read_config(cwb_id=cwb_id, init=True)

    return corpus_config


def init_corpus(corpus_config):

    current_app.logger.info(
        'initializing corpus "%s"' % corpus_config['resources']['cwb_id']
    )

    corpus = Corpus(
        corpus_name=corpus_config['resources']['cwb_id'],
        lib_path=corpus_config['resources'].get('lib_path', None),
        registry_path=current_app.config['REGISTRY_PATH'],
        data_path=current_app.config['CACHE_PATH']
    )

    return corpus


######################################################
# ROUTING ############################################
######################################################
@bp.route('/', methods=('GET', 'POST'))
@login_required
def choose():

    if request.method == 'POST':
        cwb_id = request.form['corpus']
        current_app.logger.info('activating corpus "%s"' % cwb_id)
        session['corpus'] = read_config(cwb_id)
        flash(f"activated corpus {request.form['corpus']}")
        return redirect("/corpora/" + request.form['corpus'])

    corpora = Corpora(
        registry_path=current_app.config['REGISTRY_PATH']
    ).show().index

    if 'corpus' in session:
        active = session['corpus']['resources']['cwb_id']
    else:
        active = None

    return render_template('corpora/choose.html',
                           corpora=corpora,
                           active=active)


@bp.route('/<cwb_id>', methods=('GET', 'POST'))
@login_required
def corpus_config(cwb_id):

    corpus_path = os.path.join(current_app.instance_path, cwb_id)
    cfg_path = os.path.join(corpus_path, cwb_id + '.yaml')
    corpus_config = session['corpus']

    if request.method == 'POST':
        corpus_config['query'] = {
            'context': request.form.get('context', None),
            'context_break': request.form['context_break'],
            'match_strategy': request.form['match_strategy'],
            's_query': request.form['s_query']
        }
        corpus_config['display'] = {
            'p_show': request.form.getlist('p_show'),
            'p_slots': request.form['p_slots'],
            'p_text': request.form['p_text'],
            's_show': request.form.getlist('s_show')
        }
        corpus_config['meta'] = {
            's_cwb': request.form['s_cwb'],
            's_gold': request.form['s_gold'],
        }
        session['corpus'] = corpus_config

        with open(cfg_path, "wt") as f:
            yaml.dump(corpus_config, f)

        flash(f"updated settings for corpus {session['corpus']['resources']['cwb_id']}")
        return redirect("/")

    # get available corpora
    corpora = Corpora(registry_path=current_app.config['REGISTRY_PATH']).show()

    # get current corpus attributes
    corpus = init_corpus(corpus_config)
    attributes = corpus.attributes_available
    p_atts = list(attributes['attribute'][attributes['type'] == 'p-Att'].values)
    s_atts_anno = list(
        attributes['attribute'][list(attributes['annotation']) & (attributes['type'] == 's-Att')].values
    )
    s_atts_none = list(
        attributes['attribute'][([not b for b in attributes.annotation]) & (attributes['type'] == 's-Att')].values
    )

    return render_template(
        'corpora/corpus.html',
        name=cwb_id,
        p_atts=p_atts,
        s_atts_anno=s_atts_anno,
        s_atts_none=s_atts_none,
        resources=corpus_config['resources'],
        query=corpus_config['query'],
        display=corpus_config['display'],
        meta=corpus_config['meta'],
        corpora=corpora
    )
