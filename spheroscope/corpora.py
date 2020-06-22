import logging
import os
from configparser import ConfigParser

# ccc
from ccc.cwb import Corpus, Engine

# flask
from flask import Blueprint, render_template, current_app, redirect, request

# this app
from .auth import login_required


logger = logging.getLogger(__name__)
bp = Blueprint('corpora', __name__, url_prefix='/corpora')


def init_corpus(config):

    logger.info('initializing corpus')

    corpus = Corpus(
        corpus_name=config['CORPUS']['resources']['cwb_id'],
        lib_path=config['CORPUS']['resources']['lib_path'],
        registry_path=config['REGISTRY_PATH'],
        data_path=config['CACHE_PATH']
    )

    return corpus


@bp.route('/', methods=('GET', 'POST'))
@login_required
def choose():
    if request.method == 'POST':
        return redirect("/corpora/" + request.form['corpus'])
    engine = Engine(current_app.config['REGISTRY_PATH'])
    corpora = engine.show_corpora()
    if 'CORPUS' in current_app.config:
        active = current_app.config['CORPUS']['resources']['cwb_id']
    else:
        active = None
    return render_template('corpora/choose.html',
                           corpora=corpora,
                           active=active)


@bp.route('/<cwb_id>', methods=('GET', 'POST'))
@login_required
def corpus_config(cwb_id):

    # paths
    corpus_path = os.path.join(current_app.instance_path, cwb_id)
    if not os.path.isdir(corpus_path):
        os.makedirs(corpus_path)
    cfg_path = os.path.join(corpus_path, cwb_id + '.cfg')

    corpus_config = ConfigParser()
    # get corpus config
    if os.path.isfile(cfg_path):
        corpus_config.read(cfg_path)
    # init config file with defaults if necessary
    else:
        corpus_config = current_app.config['CORPUS_DEFAULTS']
        corpus_config['resources']['cwb_id'] = cwb_id
        corpus_config['resources']['lib_path'] = corpus_path
        corpus_config['resources']['embeddings'] = ''
        with open(cfg_path, "wt") as f:
            corpus_config.write(f)

    # init cwb corpus
    current_app.config['CORPUS'] = corpus_config

    if request.method == 'POST':
        request.form.getlist('p_show')
        corpus_config = ConfigParser()
        corpus_config.read_dict({
            'resources': {
                'cwb_id': current_app.config['CORPUS']['resources']['cwb_id'],
                'lib_path': current_app.config['CORPUS']['resources']['lib_path'],
                'embeddings': current_app.config['CORPUS']['resources']['embeddings']
            },
            'query': {
                'match_strategy': request.form['match_strategy'],
                's_query': request.form['s_query'],
                's_context': request.form['s_context']
            },
            'display': {
                's_show': request.form.getlist('s_show'),
                'p_text': request.form['p_text'],
                'p_slots': request.form['p_slots'],
                'p_show': request.form.getlist('p_show')
            }
        })
        current_app.config['CORPUS'] = corpus_config
        with open(cfg_path, "wt") as f:
            corpus_config.write(f)

    # check corpus attributes
    corpus = Corpus(cwb_id)
    a = corpus.attributes_available
    p_atts = list(a.name[a.att == 'p-Att'].values)
    s_atts_anno = list(a.name[list(a.annotation) & (a.att == 's-Att')].values)
    s_atts_none = list(
        a.name[([not b for b in a.annotation]) & (a.att == 's-Att')].values
    )

    return render_template('corpora/corpus.html',
                           name=cwb_id,
                           p_atts=p_atts,
                           s_atts_anno=s_atts_anno,
                           s_atts_none=s_atts_none,
                           resources=dict(corpus_config.items('resources')),
                           query=dict(corpus_config.items('query')),
                           display=dict(corpus_config.items('display')))
