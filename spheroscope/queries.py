#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from ccc.cqpy import run_query

from flask import (
    Blueprint, redirect, render_template, request, url_for, current_app, g, session
)

from flask.cli import with_appcontext
import click

from .auth import login_required
from .corpora import read_config, init_corpus
from .database import Query

import re
import json
from pandas import DataFrame
from collections import defaultdict

import pandas as pd

bp = Blueprint('queries', __name__, url_prefix='/queries')


PATH_META = (
    "/home/ausgerechnet/corpora/cwb/upload/brexit/brexit-preref-rant/"
    "brexit_v20190522_dedup.tsv.gz"
)


def run(id, cwb_id):

    # get query
    query = Query.query.filter_by(id=id).first().serialize()

    # get corpus config
    corpus_config = read_config(cwb_id)

    # make sure anchors are int
    corrections_int = dict()
    for k in query['anchors']['corrections'].keys():
        c = query['anchors']['corrections'][k]
        corrections_int[int(k)] = c
    query['anchors']['corrections'] = corrections_int

    # load query and display parameters
    query['query'] = dict(corpus_config['query'])
    query['query']['context'] = None
    query['display'] = dict(corpus_config['display'])

    # run query
    corpus = init_corpus(corpus_config)
    current_app.logger.info('running query')
    lines = run_query(corpus, query)

    # add dataframes
    # (quick hack to make yuliya's queries work)
    dump = corpus.query(
        cqp_query=query['cqp'],
        context=query['query']['context'],
        context_break=query['query']['s_context'],
        corrections=query['anchors']['corrections'],
        match_strategy='longest'
    )

    dataframes = dump.concordance(
        p_show=query['display']['p_show'],
        s_show=query['display']['s_show'],
        slots=query['anchors']['slots'],
        cut_off=None,
        form='dataframe'
    )['dataframe']
    for df in dataframes:
        df['match'] = False
        df['matchend'] = False

    lines['df'] = dataframes

    # result_parameters = [query[key] for key in query.keys() if key not in [
    #     'id', 'user_id', 'modified', 'pattern'
    # ]]
    # param = generate_idx(result_parameters, prefix='param-', length=10)

    # # determine path to result
    # dir_result = os.path.join(current_app.instance_path, cwb_id, 'matches', param)
    # if not os.path.isdir(dir_result):
    #     os.makedirs(dir_result)
    # path_result = os.path.join(dir_result, query['name'] + ".tsv.gz")

    # # save result
    # current_app.logger.info('saving result')
    # conc.to_csv(path_result, sep="\t")

    return lines


######################################################
# ROUTING ############################################
######################################################

@bp.route('/')
@login_required
def index():
    queries = Query.query.order_by(Query.name).all()
    return render_template('queries/index.html',
                           queries=queries)


@bp.route('/<int:id>/<name>/matches', methods=('GET','POST'))
@login_required
def matches(id, name):

    # beta = request.args.get('beta', False)

    query_id = id
    query_name = name

    query_table = run_cmd(query_id)
    frequency_table = frequency_table_list(query_id)
    match_extra_inf = match_extra(query_id)

    selected_query = select_query(query_id)
    meta_data = open_meta_data(query_id)

    return render_template('queries/matches.html', query_table=query_table, match_extra_inf=match_extra_inf,
                           query_name=query_name, frequency_table=frequency_table, selected_query=selected_query,
                           meta_data=meta_data)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    # get corpus info (path)
    cwb_id = session['corpus']['resources']['cwb_id']

    if request.method == 'POST':

        query = Query(
            cqp=request.form['query'],
            name=request.form['name'],
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace(
                "None", "null"
            ),
            corrections=request.form['corrections'].replace(
                "None", "null"
            ),
            path=os.path.join(
                current_app.instance_path, cwb_id, 'queries',
                request.form['name'] + ".txt"
            ),
            user_id=g.user.id
        )
        query.write()

        return redirect(url_for('queries.index'))

    return render_template('queries/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    query = Query.query.filter_by(id=id).first()

    if request.method == 'POST':

        query = Query(
            id=id,
            user_id=g.user.id,
            cqp=request.form['query'],
            name=request.form['name'],
            pattern_id=request.form['pattern'],
            slots=request.form['slots'].replace(
                "None", "null"
            ),
            corrections=request.form['corrections'].replace(
                "None", "null"
            ),
            path=query.path
        )

        query.delete()
        query.write()
        return redirect(url_for('queries.index'))

    return render_template('queries/update.html',
                           query=query)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_cmd(id):
    query = Query.query.filter_by(id=id).first()
    query.delete()
    return redirect(url_for('queries.index'))


@bp.route('/<int:id>/query', methods=('GET',))
#@login_required
def select_query(id):

    shown_query = Query.query.filter_by(id=id).first()
    return render_template('queries/query.html',
                           shown_query=shown_query)

@bp.route('/extra', methods=('GET',))
#@login_required
def concordance_extra():

    concordance = request.json("concordance")
    # print(concordance)

    return render_template('queries/extra.html', concordance=concordance)

@bp.route('/<int:id>/run', methods=('GET', 'POST'))
def get_beta():

    return request.args.get('beta', False)

@bp.route('/<int:id>/run', methods=('GET', 'POST'))
def get_result(id):

    cwb_id = session['corpus']['resources']['cwb_id']
    result = run(id, cwb_id)
    # beta = request.args.get('beta', False)

    if result is None:
        return 'query does not have any matches'
    else:
        #return run_cmd(result, beta)
        return result

# returns query as an html table
@bp.route('/<int:id>/run', methods=('GET', 'POST'))
def run_cmd(id):

    # beta = request.args.get('beta', False)
    # cwb_id = session['corpus']['resources']['cwb_id']
    # result = run(id, cwb_id)
    result = get_result(id)
    beta = get_beta()
    # print(beta)

    #if result is None:
    #    return 'query does not have any matches'

    # print(str(result["0_lemma"].value_counts()))

    # for testing purposes:
    # result.to_pickle("table_raw_df.pkl")

    display_columns = [x for x in result.columns if x not in [
        'context_id', 'context', 'contextend'
    ]]

    display_columns2 = [x for x in result.columns if x not in ['df']]

    if not beta:

        return result[display_columns].to_html(escape=False)

    else:
        # result[display_columns2].to_html("query_result_raw.html", escape=False)
        query_df_to_json = result.to_json()
        query_json = json.loads(query_df_to_json)
        query_json["text"] = query_json["word"]

        tooltip_counter = 0

        # loop over every tweet/row
        # tweet ids: query_json["tweet_id"]["(372795, 372805)"]
        for row_id in query_json["text"]:

            # Metadaten => result['df'].iloc[tweet_id]
            # df_to_str = str(result['df'].iloc[tweet_id])

            regions = []

            for col in query_json:
                if re.findall(r'\d\_\w+', col):
                    regions.append(col)

            # txt = (tbl["text"][idx]).lower()  # <- pure Tweet

            # find all words and the match range
            cpos_dict = query_json["df"][row_id]["word"]
            match_dict = query_json["df"][row_id]["match"]
            matchend_dict = query_json["df"][row_id]["matchend"]

            # temporary list for text after annotation
            # before putting it back together
            finalize_for_frontend = []

            # find all anchor points ai for this query
            anchor_points = []
            for i in query_json["df"][row_id]:
                if re.findall(r'\b\d+\b', i):
                    anchor_points.append(["a" + str(i)])

            # annotate with html tags
            for c_pos in cpos_dict:

                word = cpos_dict[c_pos]
                w_pos = c_pos

                is_matchbeg = match_dict[c_pos]
                is_matchend = matchend_dict[c_pos]

                anchor_points_in = [
                    ai[0] for ai in anchor_points if query_json["df"][row_id][str(ai[0])[-1]][w_pos]
                ]

                prepare_for_frontend = [word, w_pos, is_matchbeg, is_matchend, anchor_points_in]

                if is_matchbeg:
                    prepare_for_frontend.insert(0, '<span class="match-highlight row-{tooltip_counter}">'.format(tooltip_counter=tooltip_counter))
                elif is_matchend:
                    prepare_for_frontend.insert(5, '</span>')

                for i in anchor_points_in:

                    if int(i[-1]) % 2 == 0:
                        prepare_for_frontend.insert(prepare_for_frontend.index(word),
                                                    '<sub class="anchor">{s}</sub>'.format(s=i[-1]))
                        if len(regions) > 0:
                            prepare_for_frontend.insert(prepare_for_frontend.index(word),
                                                        '<span class="anchor-highlight">')
                    elif int(i[-1]) % 2 != 0:
                        if len(regions) > 0:
                            prepare_for_frontend.insert(prepare_for_frontend.index(word) + 1, '</span>')
                        prepare_for_frontend.insert(prepare_for_frontend.index(word) + 1,
                                                    '<sub class="anchor">{s}</sub>'.format(s=i[-1]))

                prepare_for_frontend.remove(w_pos)
                prepare_for_frontend.remove(is_matchbeg)
                prepare_for_frontend.remove(is_matchend)
                prepare_for_frontend.remove(anchor_points_in)

                # putting together tweet with
                # finished html tags
                for part in prepare_for_frontend:
                    finalize_for_frontend.append(part)

            res = ' '.join(finalize_for_frontend)
            res = '<div class="text-content"><br>' + res

            res += '</div>'

            res += '<br>' \
                   '<button class="meta-data-button collapsible">Show Meta Data (collapsing)</button>'\
                   '<div class="query-row collapse-content-md {tw_id}"></div>'.format(tw_id="coll-"+query_json["tweet_id"][row_id])

            res += '<br>' \
                   '<button data-puw-target="#{tw_id}-modal" class="meta-data-button puw-button">Show Meta Data (pop-up window)</button>'\
                   '<div class="pop-up-window" id={tw_id}-modal>' \
                   '    <div class="puw-header">' \
                   '        <div class="puw-title">Meta Data</div>' \
                   '        <button data-close-button class="close-puw">&times;</button>' \
                   '    </div>' \
                   '    <div class="query-row puw-content-md {tw_id}"></div>' \
                   '</div>'.format(tw_id="puw-"+query_json["tweet_id"][row_id])

            query_json["text"][row_id] = res
            tooltip_counter += 1

        frontend_ready = DataFrame.from_dict(query_json)
        display_columns = ['text']

        # display_columns3 = [x for x in frontend_ready.columns if x not in ['df']]
        # frontend_ready[display_columns3].to_html("query_result_ready.html", escape=False)
        return frontend_ready.to_html(escape=False, table_id="query-results", header=False,
                                      border=0, columns=display_columns)


# function to extract extra information for every query match and convert
# it to an html table for the frontend
def match_extra(id):

    #cwb_id = session['corpus']['resources']['cwb_id']
    #result = run(id, cwb_id)
    result = get_result(id)

    #if result is None:
    #    return 'query does not have any matches'

    to_json = result.to_json()
    tbl = json.loads(to_json)
    tbl["text"] = tbl["word"]
    tweet_id = 0
    display_extra_information = {}
    display_columns = ["lemma", "offset", "word"]

    for row_id in tbl["text"]:
        df_to_html = result['df'].iloc[tweet_id].to_html(escape=False, columns=display_columns, border=0)
        display_extra_information[tweet_id] = df_to_html
        tweet_id += 1

    extra_tooltip = json.dumps(display_extra_information)

    return extra_tooltip


# function to convert frequency tables to html table
# for the frontend
def frequency_table_list(id):

    # df['x_lemma'].value_counts()
    # x steht für eine Region z.B. vom Ankerpunkt 0 bis 1

    result = get_result(id)

    #if result is None:
    #    return 'query does not have any matches'

    query_df_to_json = result.to_json()
    query_json = json.loads(query_df_to_json)

    freq_tables = []
    regions = []

    for col in query_json:
        if re.findall(r'\d\_\w+', col):
            regions.append(col)

    for region in regions:
        freq_tables.append(result[region].value_counts().to_frame().to_html(escape=False, classes="freq-table",
                                                                            border=0))

    # freq = ''.join(freq_tables)

    return ''.join(freq_tables)


# function to load and convert all meta data from the query to an html table
# for the frontend
def open_meta_data(id):

    # meta data: brexit_v20190522_dedup.tsv
    # hardcoded for now
    # meta data in /usr/local/share/cqpweb/upload

    result = get_result(id)

    #if result is None:
    #    return 'query does not have any matches'

    query_df_to_json = result.to_json()
    query_json = json.loads(query_df_to_json)

    match_tweet_id_with_meta_data = {}

    # load meta data from tsv and convert to df

    meta_data_df = pd.read_csv(PATH_META, sep='\t', header=0, low_memory=False)

    # convert meta data data frames to html table and link
    # to every tweet
    #df_to_html = ""
    tweet_id = ""
    query_json["text"] = query_json["word"]
    for row_id in query_json["text"]:

        tweet_id = query_json["tweet_id"][row_id]

        df_to_html = meta_data_df.loc[meta_data_df.id == tweet_id,
                                      meta_data_df.columns != "path"].to_html(classes="md-table", header=True,
                                                                              index=False, border=0, table_id="md-"+tweet_id)
        # df_to_html = meta_data_df.loc[meta_data_df.id == tweet_id].to_html(classes="md-table", escape=False, border=0)
        match_tweet_id_with_meta_data[tweet_id] = df_to_html

    #print(df_to_html)
    #pd.set_option('display.max_colwidth', old_width)
    #meta_data_df.loc[meta_data_df.id == tweet_id,
    #                 meta_data_df.columns != "path"].to_html("meta_data_example.html", classes="md-table", header=True,
    #                                                         border=0)
    #meta_data_df.loc[meta_data_df.id == tweet_id].to_html("meta_data_example_2.html", escape=False)

    #print(tweet_id)
    #print(len(match_tweet_id_with_meta_data))
    meta_data_for_tweet = json.dumps(match_tweet_id_with_meta_data)

    return meta_data_for_tweet


@click.command('query')
@click.argument('dir_out')
@click.argument('pattern', default=None, required=False)
@with_appcontext
def query_command(pattern, dir_out):

    os.makedirs(dir_out, exist_ok=True)

    # get all queries belonging to the pattern
    if pattern is None:
        queries = Query.query.all()
        current_app.logger.info(
            "%d queries" % len(queries)
        )
        path_summary = os.path.join(dir_out, "summary.tsv")
    else:
        queries = Query.query.filter_by(pattern_id=pattern).all()
        current_app.logger.info(
            "pattern %s: %d queries" % (str(pattern), len(queries))
        )
        path_summary = os.path.join(dir_out, str(pattern) + "-summary.tsv")

    summary = defaultdict(list)
    for query in queries:

        current_app.logger.info(query.name)

        p_out = None
        n_hits = None
        n_unique = None

        error = ""
        try:
            lines = run(query.id, None)
        except KeyboardInterrupt:
            return
        except:
            error = sys.exc_info()[0]
            lines = None

        if lines is not None:
            p_out = os.path.join(dir_out, query.name + '.tsv')
            lines.to_csv(p_out, sep="\t")
            n_hits = len(lines)
            n_unique = len(lines.tweet_id.value_counts())
        else:
            n_hits = 0
            n_unique = 0

        query_pattern = "None" if query.pattern is None else query.pattern.id

        summary['query'].append(query.name)
        summary['pattern'].append(query_pattern)
        summary['n_hits'].append(n_hits)
        summary['n_unique'].append(n_unique)
        summary['path'].append(p_out)
        summary['error'].append(error)

    summary = DataFrame(summary)
    summary.to_csv(path_summary, sep="\t")
