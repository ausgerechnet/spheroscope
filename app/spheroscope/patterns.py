from flask import Blueprint, render_template

from collections import defaultdict
from pandas import read_csv
import logging

from .auth import login_required
from .queries import get_queries_from_db


logger = logging.getLogger(__name__)
bp = Blueprint('patterns', __name__, url_prefix='/patterns')


def get_patterns():

    definitions = read_csv("instance-stable/patterns.csv", index_col=0)
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


def get_pattern(id):
    patterns = get_patterns()
    for p in patterns:
        if p['id'] == id:
            pattern = p
            break
    return pattern


@bp.route('/')
@login_required
def index():
    patterns = get_patterns()
    return render_template('patterns/index.html',
                           patterns=patterns)


@bp.route('/<int(signed=True):id>/show_pattern', methods=('GET', 'POST'))
@login_required
def show_pattern(id):
    pattern = get_pattern(id)
    return render_template('patterns/show_pattern.html',
                           pattern=pattern)
