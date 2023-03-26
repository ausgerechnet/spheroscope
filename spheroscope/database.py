#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from glob import glob

import click
from ccc.cqpy import cqpy_dump, cqpy_load
from flask import current_app
from flask.cli import with_appcontext
from pandas import read_csv
from werkzeug.security import generate_password_hash

from . import db


def get_patterns():
    # FIXME this conversion should go when the new database is in
    patterns = Pattern.query.order_by(Pattern.id).all()
    patterndict = [{
        "id": abs(p.id),
        "template": p.template,
        "explanation": p.explanation,
        "retired": p.id < 0
    } for p in patterns]
    return patterndict


class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())

    username = db.Column(db.Unicode(255), nullable=False, unique=True)
    password = db.Column(db.Unicode(255), nullable=False)


class WordList(db.Model):

    __tablename__ = 'wordlist'
    __table_args__ = (
        db.UniqueConstraint('name', 'cwb_handle', name='unique_name_cwb_handle'),
    )

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    name = db.Column(db.Unicode(255), nullable=False)
    cwb_handle = db.Column(db.Unicode(255), nullable=False)
    p_att = db.Column(db.Unicode(50), nullable=False)
    words = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    @property
    def length(self):
        return len(self.words.split("\n"))

    @property
    def path(self):
        return os.path.join("instance", self.cwb_handle, "wordlists", self.name + ".txt")

    def __repr__(self):
        return 'wordlist "%s" with %d words on attribute "%s"' % (
            self.name, self.length, self.p_att
        )

    def load(self, path):
        """ loads wordlist from specified path """

        if not os.path.isfile(path):
            current_app.logger.error('wordlist "%s" does not exist.' % path)

        # get all words as set
        words = set([w.strip() for w in open(path, "rt").read().strip().split("\n")])

        return WordList(
            name=path.split("/")[-1].split(".")[0],
            cwb_handle=path.split("/")[-3],
            words="\n".join(sorted(list(words))),
            p_att="lemma"
        )

    def write(self, write_file=True):
        """ writes wordlist to database and appropriate path """

        # add to database
        db.session.add(self)
        db.session.commit()

        # write file
        if write_file:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "wt") as f:
                f.write(self.words)

    def delete(self, delete_file=True, backup=True):
        """ deletes wordlist from database (and path) """

        # delete record from database
        current_app.logger.info('deleting wordlist "%s" from database' % self.name)
        self.query.filter_by(id=self.id).delete()
        db.session.commit()

        # delete file
        if delete_file:
            current_app.logger.info('deleting wordlist file "%s"' % self.path)
            if os.path.isfile(self.path):
                if backup:
                    os.rename(self.path, self.path + ".bak")
                else:
                    os.remove(self.path)
            else:
                current_app.logger.warning(f'file "{self.path}" does not exist, skipping delete request')


class Macro(db.Model):

    __tablename__ = 'macro'
    __table_args__ = (
        db.UniqueConstraint('name', 'cwb_handle', name='unique_name_cwb_handle'),
    )

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    name = db.Column(db.Unicode(255), nullable=False)
    cwb_handle = db.Column(db.Unicode(255), nullable=False)
    macro = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    @property
    def path(self):
        return os.path.join("instance", self.cwb_handle, "macros", self.name + ".txt")

    def __repr__(self):
        return 'macro "%s"' % (self.name)

    def load(self, path):
        """ loads macro from specified path """

        if not os.path.isfile(path):
            current_app.logger.error('macro file "%s" does not exist.' % path)

        macro = open(path, "rt").read().strip()

        return Macro(
            name=path.split("/")[-1].split(".")[0],
            cwb_handle=path.split("/")[-3],
            macro=macro
        )

    def write(self, write_file=True):
        """ writes macro to database and appropriate path """

        # add to database
        db.session.add(self)
        db.session.commit()

        # write file
        if write_file:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "wt") as f:
                f.write(self.macro)

    def delete(self, delete_file=True, backup=True):
        """ deletes macro from database (and path) """

        # delete record from database
        current_app.logger.info('deleting macro "%s" from database' % self.name)
        self.query.filter_by(id=self.id).delete()
        db.session.commit()

        # delete file
        if delete_file:
            current_app.logger.info('deleting macro file "%s"' % self.path)
            if os.path.isfile(self.path):
                if backup:
                    os.rename(self.path, self.path + ".bak")
                else:
                    os.remove(self.path)
            else:
                current_app.logger.warning(f'file "{self.path}" does not exist, skipping delete request')


class Query(db.Model):

    __tablename__ = 'query'
    __table_args__ = (
        db.UniqueConstraint('name', 'cwb_handle', name='unique_name_cwb_handle'),
    )

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pattern_id = db.Column(db.Integer, db.ForeignKey('pattern.id'))

    name = db.Column(db.Unicode(255), nullable=False)
    cwb_handle = db.Column(db.Unicode(255), nullable=False)
    corrections = db.Column(db.Unicode)
    slots = db.Column(db.Unicode)
    cqp = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)

    @property
    def path(self):
        return os.path.join("instance", self.cwb_handle, "queries", self.name + ".cqpy")

    def __repr__(self):
        return 'query "%s"' % (self.name)

    def load(self, path):
        """ loads query from specified path """

        # deal with missing and faulty files
        if not os.path.isfile(path):
            current_app.logger.error('query file "%s" does not exist.' % path)
            return None
        try:
            query = cqpy_load(path)
        except ValueError:
            current_app.logger.error('query file "%s" not a valid cqpy file' % path)
            os.rename(path, path + ".bak")
            return None
        if query is None:
            current_app.logger.error("could not load query in path %s" % path)
            return None

        return Query(
            name=query['meta'].get('name', path.split("/")[-1].split(".cqpy")[0]),
            pattern_id=query['meta'].get('pattern', '9999'),
            cqp=query['cqp'],
            cwb_handle=query['meta'].get('cwb_handle', path.split("/")[-3]),
            corrections=json.dumps(query['anchors']['corrections']),
            slots=json.dumps(query['anchors']['slots'])
        )

    def serialize(self):

        # ensure anchors in corrections are integer
        corrections = json.loads(self.corrections)
        corrections_int = dict()
        for k, c in corrections.items():
            corrections_int[int(k)] = c

        return {
            'meta': {
                'name': self.name,
                'pattern': self.pattern_id,
                'comment': self.comment
            },
            'cqp': self.cqp,
            'anchors': {
                'corrections': corrections_int,
                'slots': json.loads(self.slots)
            }
        }

    def write(self, write_file=True):
        """ writes query to database and appropriate path """

        # add to database
        db.session.add(self)
        db.session.commit()

        # write file
        if write_file:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            cqpy_dump(self.serialize(), self.path)

    def delete(self, delete_file=True, backup=True):
        """ deletes query from database (and path) """

        # delete record from database
        current_app.logger.info('deleting query "%s" from database' % self.name)
        self.query.filter_by(id=self.id).delete()
        db.session.commit()

        # delete file
        if delete_file:
            current_app.logger.info('deleting query file "%s"' % self.path)
            if os.path.isfile(self.path):
                if backup:
                    os.rename(self.path, self.path + ".bak")
                else:
                    os.remove(self.path)
            else:
                current_app.logger.warning(f'file "{self.path}" does not exist, skipping delete request')

    @property
    def pattern(self):
        return Pattern.query.filter_by(id=self.pattern_id).first()


class Pattern(db.Model):

    __tablename__ = 'pattern'

    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, nullable=False, default=datetime.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    template = db.Column(db.Unicode)
    explanation = db.Column(db.Unicode)
    retired = db.Column(db.Boolean)
    name = db.Column(db.Unicode)
    # generalizations = db.Column(db.Unicode)

    comment = db.Column(db.Unicode)


class Corpus(db.Model):

    __tablename__ = 'corpus'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('corpora', lazy=True))

    name = db.Column(db.Unicode(50))

    cwb_handle = db.Column(db.Unicode)
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
    df_patterns = read_csv(path, index_col=0, sep="\t")
    for p in df_patterns.iterrows():
        pattern = Pattern(
            id=int(p[0]),
            user_id=1,          # admin
            template=p[1]['template'],
            explanation=p[1]['explanation'],
            retired=p[1]['retired'],
            name=p[1]['name']
        )
        db.session.add(pattern)
        db.session.commit()


def import_library():

    # patterns
    path = os.path.join("library", "patterns.tsv")
    read_patterns(path)

    # wordlists
    paths = glob(os.path.join("library", "**", "wordlists", "*.txt"), recursive=True)
    for p in paths:
        wl = WordList().load(p)
        wl.user_id = 1          # admin
        wl.write()

    # macros
    paths = glob(os.path.join("library", "**", "macros", "*.txt"), recursive=True)
    for p in paths:
        macro = Macro().load(p)
        macro.user_id = 1       # admin
        macro.write()

    # queries
    paths = glob(os.path.join("library", "**", "queries", "*.cqpy"), recursive=True)
    for p in paths:
        query = Query().load(p)
        if query:
            query.user_id = 1   # admin
            query.write()


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
