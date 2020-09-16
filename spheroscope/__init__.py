#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

NAME = 'spheroscope'
DATABASE_PATH = 'spheroscope.sqlite'
CONFIG_PATH = 'spheroscope.cfg'
SECRET_KEY = 'dev'

db = SQLAlchemy()


def create_app(test_config=None):

    # create and configure app
    app = Flask(
        NAME,
        instance_relative_config=True
    )
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(
        app.instance_path, DATABASE_PATH
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        app.logger.warning("could not create instance folder")

    # read configuration if not testing
    if test_config is None:
        app.config.from_pyfile('../spheroscope.cfg')
    else:
        app.config.from_mapping(test_config)

    # ensure corpus defaults exist
    cfg_path = os.path.join(app.instance_path, 'corpus_defaults.yaml')
    if not os.path.isfile(cfg_path):
        shutil.copy(
            os.path.join('library', 'corpus_defaults.yaml'),
            cfg_path
        )

    # initialize database
    from . import database
    db.init_app(app)
    # add CLI commands
    app.cli.add_command(database.init_db_command)
    app.cli.add_command(database.import_lib_command)

    # say hello
    @app.route('/hello')
    def hello():
        return 'Hello back there!'

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

    # queries
    from . import queries
    app.register_blueprint(queries.bp)

    # patterns
    from . import patterns
    app.register_blueprint(patterns.bp)

    return app
