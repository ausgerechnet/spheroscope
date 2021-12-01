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

    # ensure corpus defaults exist
    corpus_cfg_path = os.path.join(app.instance_path, 'corpus_defaults.yaml')
    corpus_cfg_default = os.path.join('library', 'corpus_defaults.yaml')
    if not os.path.isfile(corpus_cfg_path):
        shutil.copy(corpus_cfg_default, corpus_cfg_path)

    # say hello
    @app.route('/hello')
    def hello():
        return 'Hello back there!'

    # initialize database and register CLI commands
    from . import database
    db.init_app(app)
    app.cli.add_command(database.init_db_command)
    app.cli.add_command(database.import_lib_command)

    # remote database commands
    from . import remote_db
    app.cli.add_command(remote_db.update_patterns)
    app.cli.add_command(remote_db.update_gold)

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

    # macros
    from . import macros
    app.register_blueprint(macros.bp)

    # queries and register CLI commands
    from . import queries
    app.register_blueprint(queries.bp)
    app.cli.add_command(queries.query_command)

    # patterns
    from . import patterns
    app.register_blueprint(patterns.bp)

    return app
