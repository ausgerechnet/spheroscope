import sqlite3
import json
from glob import glob

import click
from json import JSONDecodeError
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


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
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    # init with admin user
    db.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        ("admin", generate_password_hash("0000"))
    )
    db.commit()


def import_brexit():

    db = get_db()

    query_files = glob("instance-stable/queries/*.query")
    insert = (
        "INSERT INTO queries "
        "(author_id, title, query, anchors, regions, pattern) "
        "VALUES (?, ?, ?, ?, ?, ?);"
    )
    for p in query_files:
        try:
            with open(p, "rt") as f:
                query = json.loads(f.read())
        except JSONDecodeError:
            print("WARNING: not a valid query file: %s" % p)
        else:
            db.execute(insert, (1,
                                query['name'],
                                query['query'],
                                json.dumps(query['anchors']),
                                json.dumps(query['regions']),
                                query['pattern']))
            db.commit()
    print("imported queries")

    wordlists = glob("instance-stable/lib/wordlists/*.txt")
    insert = (
        "INSERT INTO wordlists "
        "(title, words, author_id) "
        "VALUES (?, ?, ?);"
    )

    for p in wordlists:
        title = p.split("/")[-1].split(".")[0]
        words = set()
        with open(p, "rt") as f:
            for line in f:
                words.add(line.rstrip())
        db.execute(insert, (title, "\n".join(words), 1))
    db.commit()

    print("imported wordlists")


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('initialized database')


@click.command('import-brexit')
@with_appcontext
def import_brexit_command():
    import_brexit()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(import_brexit_command)
