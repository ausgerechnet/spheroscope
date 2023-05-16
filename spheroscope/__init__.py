#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

NAME = 'spheroscope'
CONFIG = 'cfg.DevConfig'

db = SQLAlchemy()


def create_app(test_config=None):

    # create app
    app = Flask(NAME, instance_relative_config=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        app.logger.error("could not create instance folder")

    # read configuration if not testing
    if test_config is None:
        app.config.from_object(CONFIG)
    else:
        app.config.from_mapping(test_config)

    # init database connection
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(
            app.instance_path, app.config['DB_NAME']
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    db.init_app(app)

    # ensure corpus defaults exist
    corpus_cfg_path = os.path.join(app.instance_path, 'corpus_defaults.yaml')
    corpus_cfg_default = os.path.join('library', 'corpus_defaults.yaml')
    if not os.path.isfile(corpus_cfg_path):
        shutil.copy(corpus_cfg_default, corpus_cfg_path)

    @app.route('/hello')
    def hello():
        return 'Hello back there!'

    from . import database
    app.register_blueprint(database.bp)

    from . import remote
    app.register_blueprint(remote.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import index
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index')

    from . import corpora
    app.register_blueprint(corpora.bp)

    from . import wordlists
    app.register_blueprint(wordlists.bp)

    from . import macros
    app.register_blueprint(macros.bp)

    from . import queries
    app.register_blueprint(queries.bp)

    from . import patterns
    app.register_blueprint(patterns.bp)

    return app
