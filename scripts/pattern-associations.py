#! /usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from glob import glob

from ccc import Corpus
from ccc.discoursemes import textual_associations
from pandas import concat, read_csv


def get_tweets(corpus_name):

    c = Corpus(corpus_name)
    tweets = c.query_s_att("tweet_id")
    tweets = tweets.df[['tweet_id']].set_index('tweet_id')

    return tweets


def add_pattern_results(tweets, paths):

    for p in paths:

        pattern_name = p.split("/")[-1].split(".")[0]
        print(pattern_name)

        d = read_csv(p, sep="\t")
        if len(d) > 0:
            d = d[['tweet_id']].drop_duplicates().set_index('tweet_id')
            d[pattern_name] = True

        tweets = tweets.join(d).fillna(False)

    return tweets


def calculate_associations(tweets):

    tables = list()
    for name in tweets.columns:
        table = round(textual_associations(tweets, len(tweets), name).reset_index(), 2)
        table['node'] = name
        tables.append(table)
    tables = concat(tables)

    # post-process
    tables = tables.sort_values(by='log_likelihood', ascending=False).set_index(['node', 'candidate'])

    return tables


def main(corpus_name):

    paths = glob("instance/%s/query-results/pattern*.tsv.gz" % corpus_name)

    if len(paths) == 0:
        print('no results found; run "make query" first')
        return

    tweets = get_tweets(corpus_name)
    tweets = add_pattern_results(tweets, paths)

    tables = calculate_associations(tweets)
    tables.to_csv("instance/%s/pattern-associations.tsv" % corpus_name, sep="\t")


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--corpus_name", default="BREXIT_V20190522_DEDUP")
    args = parser.parse_args()

    main(args.corpus_name)
