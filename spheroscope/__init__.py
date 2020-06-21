import os
from flask import Flask


def create_app(test_config=None):

    # create and configure the app
    app = Flask('spheroscope', instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'spheroscope.sqlite'),
    )

    # read configuration if not testing
    if test_config is None:
        app.config.from_pyfile('../spheroscope.cfg')

        # TODO: move corpus choice to interface
        corpus_config = os.path.join('..', 'library',
                                     app.config['CORPUS'],
                                     app.config['CORPUS'] + '.cfg')
        app.config.from_pyfile(corpus_config)

    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

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

    # wordlists
    from . import wordlists
    app.register_blueprint(wordlists.bp)

    # patterns
    from . import patterns
    app.register_blueprint(patterns.bp)

    # queries
    from . import queries
    app.register_blueprint(queries.bp)

    # add run-queries command
    queries.add_run_queries(app)

    return app
