import os
from configparser import ConfigParser

# ccc
from ccc.cwb import Corpus, Corpora

# flask
from flask import Blueprint, render_template, current_app, redirect, request

# this app
from .auth import login_required


bp = Blueprint('corpora', __name__, url_prefix='/corpora')


def read_config(cwb_id):

    # corpus specific data path
    corpus_path = os.path.join(current_app.instance_path, cwb_id)
    if not os.path.isdir(corpus_path):
        os.makedirs(corpus_path)

    # corpus config
    cfg_path = os.path.join(corpus_path, cwb_id + '.cfg')
    if os.path.isfile(cfg_path):
        # read from file if exists
        corpus_config = ConfigParser()
        corpus_config.read(cfg_path)
    else:
        # init config file with defaults
        corpus_config = current_app.config['CORPUS']
        corpus_config['resources']['cwb_id'] = cwb_id
        corpus_config['resources']['lib_path'] = corpus_path
        corpus_config['resources']['embeddings'] = ''
        # save to disk
        with open(cfg_path, "wt") as f:
            corpus_config.write(f)

    return corpus_config


def activate_corpus(cwb_id):

    current_app.logger.info('activating corpus "%s"' % cwb_id)
    corpus_config = read_config(cwb_id)
    current_app.config['CORPUS'] = corpus_config


def init_corpus(corpus_config):

    current_app.logger.info('initializing corpus')

    if 'lib_path' in corpus_config['resources']:
        lib_path = corpus_config['resources']['lib_path']
    else:
        lib_path = None

    corpus = Corpus(
        corpus_name=corpus_config['resources']['cwb_id'],
        lib_path=lib_path,
        registry_path=current_app.config['REGISTRY_PATH'],
        data_path=current_app.config['CACHE_PATH']
    )

    return corpus


@bp.route('/', methods=('GET', 'POST'))
@login_required
def choose():

    if request.method == 'POST':
        activate_corpus(request.form['corpus'])
        return redirect("/corpora/" + request.form['corpus'])

    corpora = Corpora(registry_path=current_app.config['REGISTRY_PATH']).show_corpora()
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

    corpus_path = os.path.join(current_app.instance_path, cwb_id)
    cfg_path = os.path.join(corpus_path, cwb_id + '.cfg')

    if request.method == 'POST':
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

    # get corpus config
    corpus_config = current_app.config['CORPUS']

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
