import sqlite3
import logging

# flask
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
import click


logger = logging.getLogger(__name__)


def get_db():

    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):

    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():

    logger.info('initializing database')
    db = get_db()

    # read schema
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    # init admin
    db.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        ("admin", generate_password_hash("0000"))
    )

    # commit
    db.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('initialized database')


def import_lib():

    lib_path = current_app.config['LIB_PATH']

    # wordlists
    from .wordlists import wordlists_lib2db
    wordlists_lib2db(lib_path)

    # macros
    # from .wordlists import wordlists_lib2db
    # wordlists_lib2db(lib_path)
    # logger.info("imported wordlists")

    # queries
    from .queries import queries_lib2db
    queries_lib2db(lib_path)


@click.command('import-lib')
@with_appcontext
def import_lib_command():
    import_lib()
    click.echo('imported lib')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(import_lib_command)