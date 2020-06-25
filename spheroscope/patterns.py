import os
from collections import defaultdict

# requirements
from pandas import read_csv

# flask
from flask import Blueprint, render_template

# this app
from .auth import login_required
from .db import get_db
from .queries import get_queries_from_db


bp = Blueprint('patterns', __name__, url_prefix='/patterns')


def read_patterns_from_path(path):
    """ reads all patterns from specified path """

    definitions = read_csv(path, index_col=0)
    queries = get_queries_from_db()
    p2q = defaultdict(list)
    for q in queries:
        p2q[q.pop('pattern')].append(q)

    patterns = list()
    for p in p2q.keys():
        try:
            d = definitions.loc[p]
        except KeyError:
            d = {
                'template': None,
                'explanation': "uncategorized queries"
            }
        patterns.append({
            'id': p,
            'nr_queries': len(p2q[p]),
            'queries': p2q[p],
            'template': d['template'],
            'explanation': d['explanation']
        })
    patterns = sorted(patterns, key=lambda x: x['id'])
    return patterns


def read_pattern_from_db(id):
    pattern = get_db().execute(
    'SELECT pat.id, name, template, explanation, user_id, username)'
    )


def write_pattern(pattern, write_db=True):
    current_app.logger.info(
        "writing pattern %d to database" % pattern['id']
    )
    db = get_db()
    sql_insert = "INSERT INTO patterns (name"


def get_pattern(id):
    patterns = read_patterns()
    for p in patterns:
        if p['id'] == id:
            pattern = p
            break
    return pattern


def lib2db():
    path = os.path.join('library', 'patterns.csv')
    patterns = read_patterns(path)
    for p in patterns:
        pass


@bp.route('/')
@login_required
def index():
    patterns = read_patterns()
    return render_template('patterns/index.html',
                           patterns=patterns)


@bp.route('/<int(signed=True):id>/show_pattern', methods=('GET', 'POST'))
@login_required
def show_pattern(id):
    pattern = get_pattern(id)
    return render_template('patterns/show_pattern.html',
                           pattern=pattern)
