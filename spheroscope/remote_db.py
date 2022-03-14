#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from urllib.parse import quote_plus

import click
import pandas as pd
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


def connect(port=5432):

    try:
        return current_app.remote
    except AttributeError:
        current_app.logger.info(
            "connecting to remote database (%s)" % current_app.config['REMOTE_NAME']
        )

        URI = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
            host=current_app.config['REMOTE_NAME'],
            port=port,
            dbname="postgres",
            user=quote_plus(current_app.config['REMOTE_USERNAME']),
            password=quote_plus(current_app.config['REMOTE_PASSWORD'])
        )

        try:
            engine = create_engine(URI)
            connection = engine.connect()
        except OperationalError:
            current_app.logger.error("could not connect to remote database")
            return None
        else:
            current_app.logger.info("connected to remote database")
            current_app.remote = connection
            return connection


def get_tables(con):

    return list(pd.read_sql(
        "SELECT relname FROM pg_class WHERE relkind='r' AND relname !~ '^(pg_|sql_)';",
        con
    )['relname'])


def get_gold(con):

    return pd.read_sql(
        "SELECT * FROM rant.classification_gold;", con
    )


def get_patterns(con):

    patterns = pd.read_sql(
        "SELECT * FROM rant.patterns;", con, index_col='idx'
    )

    # patterns_categories = pd.read_sql(
    #     "SELECT * FROM rant.pattern_category;", con, index_col='pattern'
    # )

    # patterns_specialisations = pd.read_sql(
    #     "SELECT * FROM rant.pattern_specialisation;", con
    # )

    return patterns


def set_query_results(con):

    # - Die Queries betrachtet die DB als Annotatoren: query matches sin einträge in der classification Tabelle.
    # - Was die "echten" Annotationen unterscheidet ist, dass das  'manual' Feld bei denen true ist.
    # - Insofern musst du nur ein Insert machen mit
    # tweet = tweet_id
    # pattern = pattern_id
    # annotator = query_name
    # manual = False
    # annotation = True

    # Je nachdem was wir wollen sollte man vorher alle Annotationen
    # der zugehörigen Query löschen dass nur noch die aktuellen drin
    # sind. Dannach muss dann noch die Materialized View
    # virtual_tweet_sets refreshed werden und die zieht dann
    # automatisch die Samples und so.

    pass


@click.command('update-patterns')
@with_appcontext
def update_patterns():
    con = connect()
    if con is not None:
        patterns = get_patterns(con).sort_values(by=["retired", "idx"])
        patterns.to_csv(
            os.path.join("library", "patterns.tsv"), sep="\t"
        )


@click.command('update-gold')
@click.argument('cwb_id', default="BREXIT_V20190522_DEDUP")
@with_appcontext
def update_gold(cwb_id):
    con = connect()
    if con is not None:
        gold = get_gold(con)
        gold['tweet'] = gold['tweet'].apply(lambda x: 't' + str(x))
        # last_adjudication = gold['adjudication'].max()
        # .replace(" ", "_").replace(":", "-")
        gold.to_csv(
            os.path.join("library", cwb_id, "gold", "adjudicated.tsv"), sep="\t"
        )
