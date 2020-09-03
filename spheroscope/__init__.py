import os
from configparser import ConfigParser
from flask import Flask


def create_app(test_config=None):

    # create and configure the app
    app = Flask('spheroscope', instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'spheroscope.sqlite'),
    )

    try:
        # ensure the instance folder exists
        if not os.path.isdir(app.instance_path):
            os.makedirs(app.instance_path)
    except OSError:
        pass

    # read configuration if not testing
    if test_config is None:
        app.config.from_pyfile('../spheroscope.cfg')
    else:
        app.config.from_mapping(test_config)

    # load corpus settings
    cfg_path = os.path.join(app.instance_path, 'corpus_defaults.cfg')
    corpus_config = ConfigParser()
    if os.path.isfile(cfg_path):
        corpus_config.read(cfg_path)
    else:
        # copy defaults from master
        cfg_default = os.path.join('library', 'corpus_defaults.cfg')
        corpus_config.read(cfg_default)
        with open(cfg_path, "wt") as f:
            corpus_config.write(f)
    # save in current config
    app.config['CORPUS'] = corpus_config

    # say hello
    @app.route('/hello')
    def hello():
        return 'Hello back there!'

    # initialize database
    from . import db
    db.init_app(app)

    # authentication
    from . import auth
    app.register_blueprint(auth.bp)

    # index
    from . import index
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index')

    # corpora
    from . import corpora
    app.register_blueprint(corpora.bp)

    # wordlists
    from . import wordlists
    app.register_blueprint(wordlists.bp)

    # wordlists
    from . import macros
    app.register_blueprint(macros.bp)

    # # patterns
    # from . import patterns
    # app.register_blueprint(patterns.bp)

    # queries
    from . import queries
    app.register_blueprint(queries.bp)

    from . import newqueries
    app.register_blueprint(newqueries.bp)

    # # add run-queries command
    # queries.add_run_queries(app)

    return app
