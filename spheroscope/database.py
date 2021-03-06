#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from glob import glob
from pandas import read_csv
from datetime import datetime

from ccc.queries import cqpy_load, cqpy_dump

from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
import click

from . import db


class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    username = db.Column(db.Unicode(255), nullable=False, unique=True)
    password = db.Column(db.Unicode(255), nullable=False)


class WordList(db.Model):

    __tablename__ = 'wordlist'

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    path = db.Column(db.Unicode, nullable=False)

    name = db.Column(db.Unicode(255), nullable=False, unique=True)
    p_att = db.Column(db.Unicode(50), nullable=False)
    words = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    @property
    def length(self):
        return len(self.words.split("\n"))

    def __repr__(self):
        return 'wordlist "%s" with %d words on attribute "%s"' % (
            self.name, self.length, self.p_att
        )

    def load(self, path):
        """ loads wordlist from specified path """

        if not os.path.isfile(path):
            current_app.logger.error('wordlist "%s" does not exist.' % path)

        # determine name from path
        name = path.split("/")[-1].split(".")[0]
        # determine p-attribute from name
        p_att = "pos_ark" if name.startswith("tag") else "lemma"
        # get all words
        words = set([
            w.lstrip().rstrip() for w in open(path, "rt").read().split("\n")
        ])

        return WordList(
            name=name,
            path=path,
            words="\n".join(sorted(list(words))),
            p_att=p_att
        )

    def write(self, write_file=True):
        """ writes wordlist to database and appropriate path """

        # write record to database
        current_app.logger.info(
            'writing wordlist "%s" to database' % self.name
        )
        db.session.add(self)
        db.session.commit()

        # write file
        if write_file:
            current_app.logger.info(
                'writing wordlist "%s" to "%s"' % (self.name, self.path)
            )
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "wt") as f:
                f.write(self.words)

    def delete(self, delete_file=True):
        """ deletes wordlist from database and path """

        # delete record from database
        current_app.logger.info(
            'deleting wordlist "%s" from database' % self.name
        )
        self.query.filter_by(id=self.id).delete()
        db.session.commit()

        # delete file
        if delete_file:
            current_app.logger.info(
                'deleting wordlist file "%s"' % self.path
            )
            if os.path.isfile(self.path):
                os.remove(self.path)
            else:
                current_app.logger.warning(
                    "file does not exist, skipping delete request"
                )


class Macro(db.Model):

    __tablename__ = 'macro'

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    path = db.Column(db.Unicode, nullable=False)

    name = db.Column(db.Unicode(255), nullable=False)
    macro = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    def __repr__(self):
        return 'macro "%s"' % (self.name)

    def load(self, path):
        """ loads macro from specified path """

        if not os.path.isfile(path):
            current_app.logger.error('macro file "%s" does not exist.' % path)

        # determine name from path
        name = path.split("/")[-1].split(".")[0]
        macro = open(path, "rt").read()

        return Macro(
            name=name,
            path=path,
            macro=macro
        )

    def write(self, write_file=True):
        """ writes macro to database and appropriate path """

        # write record to database
        current_app.logger.info(
            'writing macro "%s" to database' % self.name
        )
        db.session.add(self)
        db.session.commit()

        # write file
        if write_file:
            current_app.logger.info(
                'writing macro "%s" to "%s"' % (self.name, self.path)
            )
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "wt") as f:
                f.write(self.macro)

    def delete(self, delete_file=True):
        """ deletes macro from database and path """

        # delete record from database
        current_app.logger.info(
            'deleting macro "%s" from database' % self.name
        )
        self.query.filter_by(id=self.id).delete()
        db.session.commit()

        # delete file
        if delete_file:
            current_app.logger.info(
                'deleting macro file "%s"' % self.path
            )
            if os.path.isfile(self.path):
                os.remove(self.path)
            else:
                current_app.logger.warning(
                    "file does not exist, skipping delete request"
                )


class Query(db.Model):

    __tablename__ = 'query'

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pattern_id = db.Column(db.Integer, db.ForeignKey('pattern.id'))

    path = db.Column(db.Unicode, nullable=False)

    name = db.Column(db.Unicode(255), nullable=False)
    corrections = db.Column(db.Unicode)
    slots = db.Column(db.Unicode)
    cqp = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    def __repr__(self):
        return 'query "%s"' % (self.name)

    def load(self, path):
        """ loads query from specified path """

        current_app.logger.info('loading query file "%s".' % path)
        if not os.path.isfile(path):
            current_app.logger.error('query file "%s" does not exist.' % path)

        query = cqpy_load(path)

        if query is None:
            current_app.logger.error(
                "could not load query in path %s" % path
            )
            return None

        return Query(
            name=query['meta']['name'],
            pattern_id=query['meta']['pattern'],
            cqp=query['cqp'],
            corrections=json.dumps(query['anchors']['corrections']),
            slots=json.dumps(query['anchors']['slots']),
            path=path
        )

    def serialize(self):
        return {
            'meta': {
                'name': self.name,
                'pattern': self.pattern_id,
                'comment': self.comment
            },
            'cqp': self.cqp,
            'anchors': {
                'corrections': json.loads(self.corrections),
                'slots': json.loads(self.slots)
            }
        }

    def write(self, write_file=True):
        """ writes query to database and appropriate path """

        # write record to database
        current_app.logger.info(
            'writing query "%s" to database' % self.name
        )
        db.session.add(self)
        db.session.commit()

        # write file
        if write_file:
            current_app.logger.info(
                'writing query "%s" to "%s"' % (self.name, self.path)
            )
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "wt") as f:
                f.write(cqpy_dump(self.serialize()))

    def delete(self, delete_file=True):
        """ deletes query from database and path """

        # delete record from database
        current_app.logger.info(
            'deleting query "%s" from database' % self.name
        )
        self.query.filter_by(id=self.id).delete()
        db.session.commit()

        # delete file
        if delete_file:
            current_app.logger.info(
                'deleting query file "%s"' % self.path
            )
            if os.path.isfile(self.path):
                os.remove(self.path)
            else:
                current_app.logger.warning(
                    "file does not exist, skipping delete request"
                )

    @property
    def pattern(self):
        return Pattern.query.filter_by(id=self.pattern_id).first()


class Pattern(db.Model):

    __tablename__ = 'pattern'

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    template = db.Column(db.Unicode)
    explanation = db.Column(db.Unicode)
    generalizations = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    @property
    def nr_queries(self):
        queries = Query.query.filter_by(pattern_id=self.id).all()
        return len(queries)

    @property
    def preamble(self):
        preamble = self.query.filter_by(id=-9999).first()
        return preamble.template

    def __repr__(self):
        return 'pattern %d with %d queries' % (self.id, self.nr_queries)


class Corpus(db.Model):

    __tablename__ = 'corpus'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('corpora', lazy=True))

    name = db.Column(db.Unicode(50))

    cwb_id = db.Column(db.Unicode)
    lib_path = db.Column(db.Unicode)
    embeddings = db.Column(db.Unicode)

    attribute = db.Column(db.Unicode)


#########################################
# DATABASE INIT #########################
#########################################
def init_db():

    db.drop_all()
    db.create_all()
    db.session.add(User(
        username=current_app.config['DB_USERNAME'],
        password=generate_password_hash(current_app.config['DB_PASSWORD'])
    ))
    db.session.commit()


def read_patterns(path):

    # read all the patterns in the csv
    df_patterns = read_csv(path, index_col=0)
    for p in df_patterns.iterrows():
        pattern = Pattern(
            id=int(p[0]),
            user_id=1,          # admin
            template=p[1]['template'],
            explanation=p[1]['explanation'],
            generalizations=p[1]['specialises']
        )
        current_app.logger.info(
            'writing pattern %d to database' % pattern.id
        )
        db.session.add(pattern)
        db.session.commit()


def import_library():

    # wordlists
    paths = glob(os.path.join("library", "**", "wordlists", "*.txt"), recursive=True)
    for p in paths:
        wl = WordList().load(p)
        wl.path = wl.path.replace("library", "instance")
        wl.user_id = 1          # admin
        wl.write()

    # macros
    paths = glob(os.path.join("library", "**", "macros", "*.txt"), recursive=True)
    for p in paths:
        macro = Macro().load(p)
        macro.path = macro.path.replace("library", "instance")
        macro.user_id = 1       # admin
        macro.write()

    # queries
    paths = glob(os.path.join("library", "**", "queries", "*.cqpy"), recursive=True)
    for p in paths:
        query = Query().load(p)
        query.path = query.path.replace("library", "instance")
        query.user_id = 1       # admin
        query.write()

    # patterns
    path = os.path.join("library", "patterns.csv")
    read_patterns(path)


#########################################
# CLI ###################################
#########################################
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('initialized database')


@click.command('import-lib')
@with_appcontext
def import_lib_command():
    """Import library from master."""
    import_library()
    click.echo('imported lib')
