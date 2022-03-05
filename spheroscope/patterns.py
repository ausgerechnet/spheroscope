#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from collections import defaultdict

import click
from flask import (Blueprint, current_app, jsonify, render_template, request,
                   session)
from flask.cli import with_appcontext
from pandas import DataFrame, concat

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Pattern, Query, get_patterns
from .queries import (add_gold, create_subcorpus, evaluate,
                      patch_query_results, run_queries)

bp = Blueprint('patterns', __name__, url_prefix='/patterns')


def hierarchical_query(p1, slot, p2):
    """execute a hierarchical query: retrieve matches of all queries
    belonging to a _base_ pattern, then run all queries belonging to
    _slot_ pattern on one slot defined in the base pattern.
    ---

    :param int p1: base pattern number
    :param str slot: slot name
    :param int p2: slot pattern

    """

    # make sure slot is a string
    slot = str(slot)

    # process request parameters
    cwb_id = session['corpus']['resources']['cwb_id']
    base_queries = Query.query.filter_by(pattern_id=p1).order_by(Query.name).all()
    slot_pattern = p2
    slot_queries = Query.query.filter_by(pattern_id=slot_pattern).all()

    # run all queries belonging to base pattern
    matches = run_queries(base_queries, cwb_id)
    corpus_config = read_config(cwb_id)
    matches = matches.reset_index().set_index(
        dict(corpus_config['display'])['s_show'][0]
    )

    # activate NQR
    df_dump = create_subcorpus(matches, slot)
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    name = "Pattern%dSlot%s" % (p1, slot)
    corpus.activate_subcorpus(name, df_dump)

    # run all queries belonging to slot pattern on activated NQR
    concs = list()
    for query in slot_queries:

        current_app.logger.info(query.name)
        query = query.serialize()
        dump = corpus.query(
            cqp_query=query['cqp'],
            context=corpus_config['query']['context'],
            context_break=corpus_config['query']['context_break'],
            corrections=query['anchors']['corrections'],
            match_strategy=corpus_config['query']['match_strategy']
        )
        conc = dump.concordance(
            form='slots',
            p_show=dict(corpus_config['display'])['p_show'],
            s_show=dict(corpus_config['display'])['s_show'],
            cut_off=None,
            slots=query['anchors']['slots']
        )
        conc['name'] = query['meta']['name']
        concs.append(conc)

    # post-process
    if len(concs) > 0:
        conc_slot = concat(concs)
        conc_slot = conc_slot.reset_index()
        d = conc_slot[
            ["_".join([s, p]) for p in corpus_config['display']['p_show']
             for s in query['anchors']['slots']] +
            dict(corpus_config['display'])['s_show']
        ]
        renames = dict([
            ("_".join([s, p]), ".".join([str(slot), "_".join([s, p])]))
            for p in corpus_config['display']['p_show']
            for s in query['anchors']['slots']
        ])
        d = d.rename(columns=renames).set_index(
            dict(corpus_config['display'])['s_show'][0]
        )
        result = matches.join(d, how='inner')
    else:
        result = None

    return result


######################################################
# ROUTING ############################################
######################################################
@bp.route('/')
@login_required
def index():
    """
    list all patterns that are not deprecated
    ---

    """
    patterns = Pattern.query.filter(Pattern.id >= 0).order_by(Pattern.id).all()

    return render_template('patterns/index.html',
                           patterns=patterns)


@bp.route('/api')
@login_required
def patterns():
    """
    get all patterns as json
    ---

    """

    patterndict = get_patterns()

    return jsonify(patterndict)


@bp.route('/<int(signed=True):id>', methods=('GET', 'POST'))
@login_required
def pattern(id):
    """
    get one pattern
    ---
    parameters:
      - name: id
        in: path

    """

    pattern = Pattern.query.filter_by(id=id).first()
    patterns = Pattern.query.all()
    pattern.queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    slotfinder = re.compile(r"\d+")
    pattern.slots = set(slotfinder.findall(pattern.template))

    return render_template('patterns/pattern.html',
                           pattern=pattern,
                           patterns=patterns)


@bp.route('/<int(signed=True):id>/matches', methods=('GET', 'POST'))
@login_required
def matches(id):
    """retrieve matches of all queries belonging to one pattern
    ---
    parameters:
      - name: id
        in: path

    """

    # mapping of s-att that contains gold annotation
    s_cwb = 'tweet_id'
    s_gold = 'tweet'

    # get matches
    cwb_id = session['corpus']['resources']['cwb_id']
    queries = Query.query.filter_by(pattern_id=id).order_by(Query.name).all()
    matches = run_queries(queries, cwb_id)

    # add gold
    matches = add_gold(matches, cwb_id, id, s_cwb, s_gold)
    tps = evaluate(matches, s_cwb)

    # patch for frontend
    result = patch_query_results(matches)

    return render_template('queries/standalone_result_table.html',
                           result=result,
                           tps=tps)


@bp.route('/<int(signed=True):p1>/matches/subquery', methods=('GET', 'POST'))
@login_required
def subquery(p1):
    """execute a hierarchical query: retrieve matches of all queries
    belonging to a _base_ pattern, then run all queries belonging to
    _slot_ pattern on one slot defined in the base pattern.
    ---
    parameters:
      - name: id
        in: path
        type: int
        required: true
        description: base pattern id
      - name: slot
        in: query
        type: int
        required: true
        description: name of the slot
      - name: p2
        in: query
        type: int
        description: id of pattern to fill slot

    """

    # mapping of s-att that contains gold annotation
    s_cwb = 'tweet_id'
    s_gold = 'tweet'

    # process request parameters
    cwb_id = session['corpus']['resources']['cwb_id']
    slot = request.args.get('slot')
    p2 = request.args.get('p2')

    # get matches
    matches = hierarchical_query(p1, slot, p2)

    # add gold
    matches = add_gold(matches, cwb_id, slot, s_cwb, s_gold)
    tps = evaluate(matches, s_cwb)

    # patch for frontend
    result = patch_query_results(matches)

    return render_template('queries/result_table.html',
                           result=result,
                           tps=tps)


#######
# CLI #
#######
@click.command('query')
@click.argument('pattern', required=False)
@click.argument('dir_out', required=False)
@click.argument('cwb_id', default="BREXIT_V20190522_DEDUP")
@with_appcontext
def query_command(pattern, dir_out, cwb_id):
    """
    CLI command for running all queries belonging to one pattern
    ---

    TODO improve using run_queries()
    """

    s_cwb = 'tweet_id'

    # output directory
    if dir_out is None:
        dir_out = os.path.join(
            current_app.instance_path, cwb_id, "results"
        )
    os.makedirs(dir_out, exist_ok=True)

    # get all queries belonging to the pattern
    if pattern is None:
        queries = Query.query.all()
        current_app.logger.info(
            "all patterns: %d queries" % len(queries)
        )
        path_summary = os.path.join(dir_out, "summary.tsv")
    else:
        queries = Query.query.filter_by(pattern_id=pattern).all()
        current_app.logger.info(
            "pattern %s: %d queries" % (str(pattern), len(queries))
        )
        path_summary = os.path.join(dir_out, str(pattern) + "-summary.tsv")

    # loop through queries
    # TODO use run_queries
    summary = defaultdict(list)
    for query in queries:

        current_app.logger.info(query.name)

        p_out = None
        n_hits = None
        n_unique = None

        # error = ""
        try:
            query = Query.query.filter_by(id=query.id).first()
            lines = run_queries([query], cwb_id)
        except KeyboardInterrupt:
            return

        if lines is not None and len(lines) > 0:
            p_out = os.path.join(dir_out, query.name + '.tsv')
            lines.to_csv(p_out, sep="\t")
            n_hits = len(lines)
            n_unique = len(lines[s_cwb].value_counts())
        else:
            n_hits = 0
            n_unique = 0

        query_pattern = "None" if query.pattern is None else query.pattern.id

        summary['query'].append(query.name)
        summary['pattern'].append(query_pattern)
        summary['n_hits'].append(n_hits)
        summary['n_unique'].append(n_unique)
        summary['path'].append(p_out)
        # summary['error'].append(error)

    summary = DataFrame(summary).set_index('query')
    summary.to_csv(path_summary, sep="\t")
