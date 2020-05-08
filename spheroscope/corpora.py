import logging

# ccc
from ccc.cwb import Corpus, Engine

# flask
from flask import Blueprint, render_template

# this app
from .auth import login_required


logger = logging.getLogger(__name__)
bp = Blueprint('corpora', __name__, url_prefix='/corpora')


def init_corpus(config):

    logger.info('initializing corpus')

    corpus = Corpus(
        corpus_name=config['CORPUS_NAME'],
        lib_path=config['LIB_PATH'],
        s_meta=config['S_META'],
        registry_path=config['REGISTRY_PATH'],
        data_path=config['CACHE_PATH']
    )

    return corpus


@bp.route('/', methods=('GET', 'POST'))
@login_required
def choose(config):
    engine = Engine(config['REGISTRY_PATH'])
    corpora = engine.show_corpora()
    return render_template('corpora/choose.html', corpora=corpora)
