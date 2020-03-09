from flask import Blueprint, render_template, current_app
import logging

from ccc.cwb import Corpus, Engine

from .auth import login_required


logger = logging.getLogger(__name__)
bp = Blueprint('corpora', __name__, url_prefix='/corpora')


def init_corpus(config, subcorpus=False):
    logger.info('initializing corpus')
    corpus = Corpus(
        corpus_name=config['CORPUS_NAME'],
        lib_path=config['LIB_PATH'],
        s_meta='tweet_id',
        registry_path=config['REGISTRY_PATH'],
        cache_path=config['CACHE_PATH']
    )

    # restrict to subcorpus
    if subcorpus:
        corpus.subcorpus_from_query(
            query="/region[tweet,a] :: (a.tweet_duplicate_status!='1') within tweet;",
            name="DEDUP"
        )

    return corpus


@bp.route('/', methods=('GET', 'POST'))
@login_required
def choose():
    engine = Engine(current_app.config['REGISTRY_PATH'])
    corpora = engine.show_corpora()
    return render_template('corpora/choose.html', corpora=corpora)
