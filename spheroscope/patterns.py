#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import click
from flask import (Blueprint, current_app, jsonify, render_template, request,
                   session)
from flask.cli import with_appcontext
from pandas import concat, DataFrame

from .auth import login_required
from .corpora import init_corpus, read_config
from .database import Pattern, Query, get_patterns
from .queries import (add_gold, create_subcorpus, evaluate,
                      patch_query_results, run_queries)

bp = Blueprint('patterns', __name__, url_prefix='/patterns')

# pattern queries nicht automatisch ausführen
# am Anfang überspringbar?
# left join der slot matches mit match, matchend?


def hierarchical_query(p1, slot, p2, s_cwb, cwb_id):
    """execute a hierarchical query: retrieve matches of all queries
    belonging to a _base_ pattern, then run all queries belonging to
    _slot_ pattern on one slot defined in the base pattern.
    ---

    :param int p1: base pattern number
    :param str slot: slot name
    :param int p2: slot pattern
    :param str s_cwb: s-attribute used for indexing

    """

    # make sure slot is a string
    slot = str(slot)

    # process request parameters
    base_queries = Query.query.filter_by(pattern_id=p1, cwb_handle=cwb_id).order_by(Query.name).all()
    slot_pattern = p2
    slot_queries = Query.query.filter_by(pattern_id=slot_pattern, cwb_handle=cwb_id).all()

    # run all queries belonging to base pattern
    matches = run_queries(base_queries, cwb_id)
    corpus_config = read_config(cwb_id)
    matches = matches.reset_index().set_index(s_cwb)

    # activate NQR
    df_dump = create_subcorpus(matches, slot)
    corpus_config = read_config(cwb_id)
    corpus = init_corpus(corpus_config)
    name = "Pattern%dSlot%s" % (p1, slot)
    corpus = corpus.activate_subcorpus(name, df_dump)

    # run all queries belonging to slot pattern on activated NQR
    concs = list()
    current_app.logger.info(f"running {len(slot_queries)} queries of slot pattern on activated NQR")
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
        conc['slot-query'] = query['meta']['name']
        concs.append(conc)

    # post-process
    if len(concs) > 0:
        conc_slot = concat(concs)
        conc_slot = conc_slot.reset_index()
        try:
            conc_slot[['slot-start', 'slot-end']] = DataFrame(conc_slot['index'].tolist())
            d = conc_slot[
                ['slot-query', 'slot-start', 'slot-end'] +
                ["_".join([s, p]) for p in corpus_config['display']['p_show'] for s in query['anchors']['slots']] +
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
        except KeyError:
            pass
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

    if 'corpus' in session:
        cwb_id = session['corpus']['resources']['cwb_id']
        pattern.queries = Query.query.filter_by(pattern_id=id, cwb_handle=cwb_id).order_by(Query.name).all()
    else:
        cwb_id = None
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
    s_cwb = session['corpus']['meta']['s_cwb']
    s_gold = session['corpus']['meta']['s_gold']

    # get matches
    cwb_id = session['corpus']['resources']['cwb_id']
    queries = Query.query.filter_by(pattern_id=id, cwb_handle=cwb_id).order_by(Query.name).all()
    matches = run_queries(queries, cwb_id)

    # add gold and evaluate
    matches = add_gold(matches, cwb_id, id, s_cwb, s_gold)
    statistics = evaluate(matches.reset_index().drop_duplicates(subset=[s_cwb, 'query']))

    # add pattern statistics (necessary due to duplicates across queries)
    pat = matches.reset_index().drop_duplicates(subset=[s_cwb])
    pat['query'] = f'pattern {id}'
    stat_pat = evaluate(pat)
    statistics = concat([statistics, stat_pat])

    # concordancing cut off: get all TPs and FPs, sample from the rest
    known = matches.loc[matches['TP'] != "?"]
    unknown = matches.loc[matches['TP'] == "?"]
    cut_off = min(int(request.args.get('cut_off', 1000)), len(unknown))
    unknown = unknown.sample(cut_off)
    concordance = concat([known, unknown])
    concordance = patch_query_results(concordance)

    current_app.logger.info("rendering result")
    return render_template('queries/standalone_result_table.html',
                           concordance=concordance,
                           statistics=statistics.to_html(
                               justify='left',
                               classes=['table', 'is-striped', 'is-hoverable', 'is-narrow', 'sortable']
                           ))


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
    s_cwb = session['corpus']['meta']['s_cwb']
    s_gold = session['corpus']['meta']['s_gold']

    # process request parameters
    cwb_id = session['corpus']['resources']['cwb_id']
    slot = request.args.get('slot')
    p2 = request.args.get('p2')

    # get matches
    matches = hierarchical_query(p1, slot, p2, s_cwb, cwb_id)

    # add gold
    matches = add_gold(matches, cwb_id, slot, s_cwb, s_gold)
    statistics = evaluate(matches, s_cwb)

    # add pattern statistics (necessary due to duplicates across queries)
    pat = matches.reset_index().drop_duplicates(subset=[s_cwb])
    pat['query'] = f'pattern {id}'
    stat_pat = evaluate(pat)
    statistics = concat([statistics, stat_pat])

    # patch for frontend
    result = patch_query_results(matches)

    # cut off
    cut_off = min(int(request.args.get('cut_off', 1000)), len(result))
    concordance = result.sample(cut_off)

    current_app.logger.info("rendering result table")
    return render_template('queries/standalone_result_table.html',
                           concordance=concordance,
                           statistics=statistics.to_html(
                               justify='left',
                               classes=['table', 'is-striped', 'is-hoverable', 'is-narrow', 'sortable']
                           ))


@bp.route('/<int(signed=True):p1>/matches/mock', methods=('GET', 'POST'))
def mock(p1):

    # request parameters
    slot = int(request.args.get('slot'))
    p2 = int(request.args.get('p2'))
    cwb_id = session['corpus']['resources']['cwb_id']

    # read
    from pandas import read_csv
    dir_out = os.path.join(current_app.instance_path, cwb_id, "query-results")
    path = os.path.join(dir_out, "pattern%d-slot%d-pattern%d-annotate.tsv" % (p1, slot, p2))
    table = read_csv(path, sep="\t")

    # format
    table['word'] = table.apply(highlight_slots, axis=1)

    # select columns
    firsts = ['word', 'tweet_id', 'query', 'query_slot', 'query_hierarchical', 'query_slot_hierarchical']
    pos = [c for c in table.columns if c.startswith("exact")]
    pos += [c for c in table.columns if c.startswith("within")]
    pos += [c for c in table.columns if c.startswith("overlap")]
    pos += [c for c in table.columns if c.startswith("outside")]

    # format
    table = table[firsts + pos]
    table.columns = ["-" * 100 + "word" + "-" * 100] + list(table.columns[1:])
    table = table.sort_values(by=["query_hierarchical", "query_slot_hierarchical", "tweet_id"])

    # return
    return render_template(
        'patterns/mock.html',
        table=table.to_html(
            escape=False,
            index=False,
            justify='left',
            classes=['table', 'is-hoverable', 'is-narrow', 'is-striped', 'sortable']
        )
    )


def add_role_of_slot(roles, context_start, slot_start, slot_end, role):

    try:
        start = slot_start - context_start
        end = slot_end - context_start + 1
        for i in range(start, end):
            roles[i].append(role)
    except IndexError:
        pass

    return roles


def highlight_slots(row):

    tokens = row['word'].split(" ")
    roles = [list() for i in range(len(tokens))]
    roles = add_role_of_slot(roles, row['context'], row["0_START"], row["0_END"], "0")
    roles = add_role_of_slot(roles, row['context'], row["1_START"], row["1_END"], "1")
    roles = add_role_of_slot(roles, row['context'], row["0_START_slot"], row["0_END_slot"], "0_slot")
    roles = add_role_of_slot(roles, row['context'], row["1_START_slot"], row["1_END_slot"], "1_slot")
    roles = add_role_of_slot(roles, row['context'], row["match"], row["matchend"], "match")
    roles = add_role_of_slot(roles, row['context'], row["match_slot"], row["matchend_slot"], "match_slot")
    # roles = [[a for a in set(r) if a is not None] for r in list(zip(*roles))]

    formatted = list()
    for t, r in zip(tokens, roles):

        style = list()

        if ("match" in r) and ("match_slot" in r):
            style.append("background-color:orange")
        elif "match" in r:
            style.append("background-color:salmon")
        elif "match_slot" in r:
            style.append("background-color:yellow")

        if "1" in r:
            style.append("text-decoration:underline")

        if "0" in r or "1" in r:
            style.append("font-weight:bold")
        if "0_slot" in r or "1_slot" in r:
            style.append("font-style:italic")

        if len(style) > 0:
            f = '<span style="' + ";".join(style) + ';">' + t + " </span>"
        else:
            f = t + " "

        formatted.append(f)

    return "".join(formatted)


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

    """

    # output directory
    if dir_out is None:
        dir_out = os.path.join(current_app.instance_path, cwb_id, "query-results")
    os.makedirs(dir_out, exist_ok=True)

    # restrict to given patterns
    patterns = Pattern.query.all() if pattern is None else Pattern.query.filter_by(id=pattern)

    for pattern in patterns:
        queries = Query.query.filter_by(pattern_id=pattern.id, cwb_handle=cwb_id).all()
        current_app.logger.info("pattern %d: %d queries" % (pattern.id, len(queries)))
        path_out = os.path.join(dir_out, "pattern%d.tsv.gz" % pattern.id)
        if len(queries) > 0:
            matches = run_queries(queries, cwb_id)
            matches.to_csv(path_out, sep="\t", compression="gzip")


@click.command('subquery')
@click.argument('base_pattern')
@click.argument('slot')
@click.argument('slot_pattern')
@click.argument('dir_out', required=False)
@click.argument('s_cwb', default='tweet_id')
@click.argument('cwb_id', default="BREXIT_V20190522_DEDUP")
@with_appcontext
def subquery_command(base_pattern, slot, slot_pattern, dir_out, s_cwb, cwb_id):
    """
    CLI command for running hierarchical queries
    ---

    """

    base_pattern = int(base_pattern)
    slot = str(slot)
    slot_pattern = int(slot_pattern)

    # output directory
    if dir_out is None:
        dir_out = os.path.join(current_app.instance_path, cwb_id, "query-results")
    os.makedirs(dir_out, exist_ok=True)
    path_out = os.path.join(dir_out, "pattern%d-slot%s-pattern%d.tsv.gz" % (base_pattern, slot, slot_pattern))

    # get matches
    matches = hierarchical_query(base_pattern, slot, slot_pattern, s_cwb, cwb_id)
    matches.to_csv(path_out, sep="\t", compression="gzip")
